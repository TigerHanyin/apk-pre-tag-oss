# -*- coding: utf-8 -*-
import oss2
import struct
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo
import logging
import tempfile
import os

# Constants
APK_SIGNATURE_SCHEME_V2_BLOCK_ID = 0x7109871a
APK_SIG_BLOCK_MAGIC_HI = 0x3234206b636f6c42
APK_SIG_BLOCK_MAGIC_LO = 0x20676953204b5041
APK_SIG_BLOCK_MIN_SIZE = 32
ZIP_EOCD_REC_MIN_SIZE = 22
ZIP_EOCD_REC_SIG = 0x06054b50
ZIP_EOCD_COMMENT_LENGTH_FIELD_OFFSET = 20
UINT16_MAX_VALUE = 65535

# Logger setup
logging.getLogger("oss2.api").setLevel(logging.ERROR)
logging.getLogger("oss2.auth").setLevel(logging.ERROR)
LOGGER = logging.getLogger()

# Custom exception
class SignatureNotFoundException(Exception):
    pass

def get_comment_length_from_oss(bucket, object_name):
    LOGGER.info('Getting comment length from OSS for object: {}'.format(object_name))
    head_info = bucket.head_object(object_name)
    archive_size = head_info.content_length

    if archive_size < ZIP_EOCD_REC_MIN_SIZE:
        raise IOError("APK too small for ZIP End of Central Directory (EOCD) record")
    
    max_comment_length = min(archive_size - ZIP_EOCD_REC_MIN_SIZE, UINT16_MAX_VALUE)
    eocd_with_empty_comment_start_position = archive_size - ZIP_EOCD_REC_MIN_SIZE
    
    data = bucket.get_object(
        object_name, byte_range=(eocd_with_empty_comment_start_position - max_comment_length, archive_size - 1)
    ).read()
    
    for expected_comment_length in range(max_comment_length + 1):
        eocd_start_pos = len(data) - ZIP_EOCD_REC_MIN_SIZE - expected_comment_length
        sig_data = data[eocd_start_pos:eocd_start_pos + 4]
        if len(sig_data) != 4:
            continue
        sig = struct.unpack('<I', sig_data)[0]
        if sig == ZIP_EOCD_REC_SIG:
            comment_length_data = data[eocd_start_pos + ZIP_EOCD_COMMENT_LENGTH_FIELD_OFFSET:eocd_start_pos + ZIP_EOCD_COMMENT_LENGTH_FIELD_OFFSET + 2]
            if len(comment_length_data) != 2:
                continue
            actual_comment_length = struct.unpack('<H', comment_length_data)[0]
            if actual_comment_length == expected_comment_length:
                return actual_comment_length
    raise IOError("ZIP End of Central Directory (EOCD) record not found")

def find_central_directory_start_offset(bucket, object_name, comment_length):
    LOGGER.info('Finding central directory start offset for object: {}'.format(object_name))
    ZIP_END_OF_CENTRAL_DIR_SIZE = 22
    OFFSET_OF_START_OF_CENTRAL_DIRECTORY = 16
    
    head_info = bucket.head_object(object_name)
    archive_size = head_info.content_length
    if archive_size < ZIP_END_OF_CENTRAL_DIR_SIZE:
        raise IOError("APK too small for ZIP End of Central Directory (EOCD) record")

    eocd_offset = archive_size - comment_length - ZIP_END_OF_CENTRAL_DIR_SIZE
    
    central_directory_offset_bytes = bucket.get_object(
        object_name,
        byte_range=(eocd_offset + OFFSET_OF_START_OF_CENTRAL_DIRECTORY, eocd_offset + OFFSET_OF_START_OF_CENTRAL_DIRECTORY + 3)
    ).read()
    
    central_dir_start_offset = struct.unpack('<I', central_directory_offset_bytes)[0]
    return central_dir_start_offset

def find_apk_signing_block(bucket, object_name, central_dir_offset):
    LOGGER.info('Finding APK signing block for object: {}'.format(object_name))
    if central_dir_offset < APK_SIG_BLOCK_MIN_SIZE:
        raise SignatureNotFoundException("APK too small for APK Signing Block. ZIP Central Directory offset: " + str(central_dir_offset))
    
    footer_size = 24
    footer_start_pos = central_dir_offset - footer_size
    footer_data = bucket.get_object(object_name, byte_range=(footer_start_pos, central_dir_offset-1)).read()
    
    footer_format = '<Q16s'
    apk_sig_block_size, magic = struct.unpack(footer_format, footer_data)
    
    if magic != struct.pack('<QQ', APK_SIG_BLOCK_MAGIC_LO, APK_SIG_BLOCK_MAGIC_HI):
        raise SignatureNotFoundException("No APK Signing Block before ZIP Central Directory")
    
    if apk_sig_block_size < footer_size or apk_sig_block_size > central_dir_offset - APK_SIG_BLOCK_MIN_SIZE:
        raise SignatureNotFoundException("APK Signing Block size out of range: " + str(apk_sig_block_size))
    
    apk_sig_block_start = central_dir_offset - apk_sig_block_size - 8
    apk_sig_block_data = bucket.get_object(object_name, byte_range=(apk_sig_block_start, central_dir_offset-1)).read()
    return apk_sig_block_data, apk_sig_block_start

def find_id_values(apk_signing_block):
    LOGGER.info('Finding ID values in APK signing block')
    pairs = apk_signing_block[8:-24]
    id_values = {}
    entry_count = 0
    i = 0
    
    while i < len(pairs):
        entry_count += 1
        if i + 8 > len(pairs):
            raise SignatureNotFoundException(f"Insufficient data to read size of APK Signing Block entry #{entry_count}")
        
        len_long = struct.unpack('<Q', pairs[i:i+8])[0]
        i += 8
        if len_long < 4 or len_long > len(pairs) - i:
            raise SignatureNotFoundException(f"APK Signing Block entry #{entry_count} size out of range: {len_long}")
        
        id = struct.unpack('<I', pairs[i:i+4])[0]
        i += 4
        len_int = int(len_long) - 4
        if len_int > len(pairs) - i:
            raise SignatureNotFoundException(f"APK Signing Block entry #{entry_count} size out of range: {len_int}, available: {len(pairs) - i}")
        
        entry_data = pairs[i:i+len_int]
        i += len_int
        id_values[id] = entry_data
    
    return id_values

def create_apk_signing_block(id_values):
    LOGGER.info('Creating APK signing block')
    signing_block_data = bytearray()
    length = 24
    
    for entry_id, entry_data in id_values.items():
        entry_total_size = len(entry_data) + 12
        length += entry_total_size
        signing_block_data.extend(struct.pack('<QI', entry_total_size - 8, entry_id))
        signing_block_data.extend(entry_data)
    
    signing_block_data = struct.pack('<Q', length) + signing_block_data
    signing_block_data += struct.pack('<Q', length)
    signing_block_data += struct.pack('<QQ', APK_SIG_BLOCK_MAGIC_LO, APK_SIG_BLOCK_MAGIC_HI)
    
    return signing_block_data, length + 8

def update_apk(bucket, object_name, central_dir_start_offset, apk_signing_block_offset, apk_signing_block_data, length, comment_length, newKey, dst_bucket):
    LOGGER.info('Updating APK for object: {}'.format(object_name))
    part_size = 5 * 1024 * 1024
    
    total_size = bucket.head_object(object_name).content_length
    num_parts = (total_size + part_size - 1) // part_size
    _, temp_local_apk_path = tempfile.mkstemp()
    
    try:
        # Download APK in parts
        with open(temp_local_apk_path, 'wb') as temp_file:
            for part_number in range(num_parts):
                start = part_number * part_size
                end = min(start + part_size, total_size) - 1
                result = bucket.get_object(object_name, byte_range=(start, end))
                temp_file.write(result.read())

        # Modify APK locally
        with open(temp_local_apk_path, 'r+b') as apk_file:
            apk_file.seek(central_dir_start_offset)
            central_dir_bytes = apk_file.read()

            apk_file.seek(apk_signing_block_offset)
            apk_file.write(apk_signing_block_data)
            apk_file.write(central_dir_bytes)
            apk_file.truncate()

            eocd_offset = apk_file.tell() - comment_length - 6
            apk_file.seek(eocd_offset)
            new_central_dir_offset = apk_signing_block_offset + length
            apk_file.write(struct.pack('<I', new_central_dir_offset))

        # Upload modified APK to OSS
        new_object_name = newKey
        headers = {
            'x-oss-meta-edgepack-offset': str(apk_signing_block_offset + length),
            'x-oss-meta-edgepack-type': 'v2'
        }
        upload_id = dst_bucket.init_multipart_upload(new_object_name, headers=headers).upload_id
        
        parts = []
        with open(temp_local_apk_path, 'rb') as fileobj:
            part_size = determine_part_size(total_size, preferred_size=100 * 1024)
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)
                result = dst_bucket.upload_part(new_object_name, upload_id, part_number,
                                                SizedFileAdapter(fileobj, num_to_upload))
                parts.append(PartInfo(part_number, result.etag))
                offset += num_to_upload
                part_number += 1
        
        dst_bucket.complete_multipart_upload(new_object_name, upload_id, parts, headers=headers)
    finally:
        os.remove(temp_local_apk_path)
