# -*- coding: utf-8 -*-
import helper
import oss2
import json
import os
import time
import logging

logging.getLogger("oss2.api").setLevel(logging.ERROR)
logging.getLogger("oss2.auth").setLevel(logging.ERROR)
LOGGER = logging.getLogger()

# Constants and Configurations
DEFAULT_DST_BUCKET_NAME = os.environ.get("DST_BUCKET_NAME")
DEFAULT_DST_ENDPOINT = os.environ.get("DST_ENDPOINT")
PROCESSED_DIR = os.environ.get("PROCESSED_DIR", "")
RETAIN_FILE_NAME = os.environ.get("RETAIN_FILE_NAME", "")
APK_SIGNING_TOOL = os.environ.get("APK_SIGNING_TOOL", "v2-Walle")
CUSTOM_BLOCK_ID = os.environ.get("CUSTOM_BLOCK_ID")

# Decorator to print execution time
def print_excute_time(func):
    def wrapper(*args, **kwargs):
        local_time = time.time()
        ret = func(*args, **kwargs)
        LOGGER.info('Function [%s] execute time is %.2f' % (func.__name__, time.time() - local_time))
        return ret
    return wrapper

def initialize_bucket(auth, endpoint, bucket_name):
    return oss2.Bucket(auth, endpoint, bucket_name)

def get_dst_bucket_name(evt):
    return os.environ.get("DST_BUCKET_NAME", evt['oss']['bucket']['name'])

def get_event_details(event):
    evt_lst = json.loads(event)
    return evt_lst['events'][0]

def resolve_symlink(bucket, object_name):
    target_key = bucket.get_symlink(object_name).target_key
    if target_key == "":
        raise RuntimeError(f'{object_name} is invalid symlink file')
    return target_key

def validate_file_type(object_name):
    file_type = os.path.splitext(object_name)[1]
    if file_type != ".apk":
        raise RuntimeError(f'{object_name} filetype is not apk')

def construct_new_key(object_name, processed_dir, retain_file_name):
    lst = object_name.split("/")
    apk_name = lst[-1]
    if processed_dir and processed_dir[-1] != "/":
        processed_dir += "/"
    if retain_file_name == "false":
        return processed_dir + apk_name
    else:
        return f"{processed_dir}{apk_name.replace('.apk', '/')}{apk_name}"

def get_placeholder():
    return bytearray(10240)  # Create a 10240-byte placeholder

def determine_new_pair_id(apk_signing_tool, custom_block_id):
    if apk_signing_tool == "v2-VasDolly":
        return 0x881155ff
    elif apk_signing_tool == "v2-Walle":
        return 0x71777777
    elif apk_signing_tool == "v2-Custom":
        if custom_block_id is None:
            raise ValueError("CUSTOM_BLOCK_ID environment variable is not set for V2-Custom.")
        try:
            return int(custom_block_id, 16)
        except ValueError:
            raise ValueError(f"The value of CUSTOM_BLOCK_ID ('{custom_block_id}') is not a valid hexadecimal number.")
    else:
        raise ValueError(f"Unsupported APK_SIGNING_TOOL: {apk_signing_tool}")

@print_excute_time
def handler(event, context):
    evt = get_event_details(event)
    creds = context.credentials
    auth = oss2.StsAuth(creds.access_key_id, creds.access_key_secret, creds.security_token)
    
    bucket_name = evt['oss']['bucket']['name']
    endpoint = 'oss-' + evt['region'] + '-internal.aliyuncs.com'
    bucket = initialize_bucket(auth, endpoint, bucket_name)
    
    object_name = evt['oss']['object']['key']
    if "ObjectCreated:PutSymlink" == evt['eventName']:
        object_name = resolve_symlink(bucket, object_name)
    
    validate_file_type(object_name)
    new_key = construct_new_key(object_name, PROCESSED_DIR, RETAIN_FILE_NAME)
    
    comment_length = helper.get_comment_length_from_oss(bucket, object_name)
    central_dir_start_offset = helper.find_central_directory_start_offset(bucket, object_name, comment_length)
    apk_sig_block_data, apk_signing_block_offset = helper.find_apk_signing_block(bucket, object_name, central_dir_start_offset)
    originId_values = helper.find_id_values(apk_sig_block_data)
    
    apk_signature_scheme_v2_block = originId_values.get(helper.APK_SIGNATURE_SCHEME_V2_BLOCK_ID)
    if apk_signature_scheme_v2_block is None:
        raise IOError("No APK Signature Scheme v2 block in APK Signing Block")
    
    new_pair_id = determine_new_pair_id(APK_SIGNING_TOOL, CUSTOM_BLOCK_ID)
    originId_values[new_pair_id] = get_placeholder()
    
    new_apk_signing_block, length = helper.create_apk_signing_block(originId_values)
    
    dst_bucket_name = get_dst_bucket_name(evt)
    dst_bucket = initialize_bucket(auth, DEFAULT_DST_ENDPOINT, dst_bucket_name)
    
    helper.update_apk(bucket, object_name, central_dir_start_offset, apk_signing_block_offset, new_apk_signing_block, length, comment_length, new_key, dst_bucket)
