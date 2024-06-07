
> 注：当前项目为 Serverless Devs 应用，由于应用中会存在需要初始化才可运行的变量（例如应用部署地区、函数名等等），所以**不推荐**直接 Clone 本仓库到本地进行部署或直接复制 s.yaml 使用，**强烈推荐**通过 `s init ${模版名称}` 的方法或应用中心进行初始化，详情可参考[部署 & 体验](#部署--体验) 。

# apk-pre-tag-oss-v3 帮助文档
<p align="center" class="flex justify-center">
    <a href="https://www.serverless-devs.com" class="ml-1">
    <img src="http://editor.devsapp.cn/icon?package=apk-pre-tag-oss-v3&type=packageType">
  </a>
  <a href="http://www.devsapp.cn/details.html?name=apk-pre-tag-oss-v3" class="ml-1">
    <img src="http://editor.devsapp.cn/icon?package=apk-pre-tag-oss-v3&type=packageVersion">
  </a>
  <a href="http://www.devsapp.cn/details.html?name=apk-pre-tag-oss-v3" class="ml-1">
    <img src="http://editor.devsapp.cn/icon?package=apk-pre-tag-oss-v3&type=packageDownload">
  </a>
</p>

<description>

使用函数计算，自动预处理上传到OSS指定前缀目录的apk文件，主要用于预处理不超过10G的单文件

</description>

<codeUrl>

- [:smiley_cat: 代码](https://github.com/TigerHanyin/apk-pre-tag-oss)

</codeUrl>
<preview>



</preview>


## 前期准备

使用该项目，您需要有开通以下服务并拥有对应权限：

<service>



| 服务/业务 |  权限  | 相关文档 |
| --- |  --- | --- |
| 函数计算 |  AliyunFCFullAccess | [帮助文档](https://help.aliyun.com/product/2508973.html) [计费文档](https://help.aliyun.com/document_detail/2512928.html) |
| OSS |  AliyunOSSFullAccess | [帮助文档](undefined) [计费文档](undefined) |

</service>

<remark>



</remark>

<disclaimers>



</disclaimers>

## 部署 & 体验

<appcenter>
   
- :fire: 通过 [Serverless 应用中心](https://fcnext.console.aliyun.com/applications/create?template=apk-pre-tag-oss-v3) ，
  [![Deploy with Severless Devs](https://img.alicdn.com/imgextra/i1/O1CN01w5RFbX1v45s8TIXPz_!!6000000006118-55-tps-95-28.svg)](https://fcnext.console.aliyun.com/applications/create?template=apk-pre-tag-oss-v3) 该应用。
   
</appcenter>
<deploy>
    
- 通过 [Serverless Devs Cli](https://www.serverless-devs.com/serverless-devs/install) 进行部署：
  - [安装 Serverless Devs Cli 开发者工具](https://www.serverless-devs.com/serverless-devs/install) ，并进行[授权信息配置](https://docs.serverless-devs.com/fc/config) ；
  - 初始化项目：`s init apk-pre-tag-oss-v3 -d apk-pre-tag-oss-v3`
  - 进入项目，并进行项目部署：`cd apk-pre-tag-oss-v3 && s deploy -y`
   
</deploy>

## 案例介绍

<appdetail id="flushContent">

#### 基本功能
在该案例中，用户可以通过上传 .apk 文件到指定的 OSS（Object Storage Service）桶（bucket），自动触发一系列函数计算（Function Compute）操作。这些操作包括预处理 .apk 文件并在另一个 OSS 桶中生成包含特定留白和偏移量的新文件。特定的偏移量通过响应头的方式传递给 CDN（Content Delivery Network）。此案例展示了如何自动化和优化应用分发的预处理工作流，并通过函数计算服务减少了人工干预。
#### 工作流程
自动触发：用户将 .apk 文件上传至 OSS 桶 A 后，自动触发函数计算服务进行后续处理。

文件预处理：函数计算服务在 OSS 桶 B 中生成对应的新文件，该文件包含特定的留白和偏移量。

响应头传递：预处理过程中生成的偏移量通过 HTTP 响应头传递给 CDN，用于优化后续文件分发。
#### 背景/适用场景
该方案特别适用于如下应用场景：

1.应用市场和软件分发平台：需要预处理和优化分发大量 APK 文件。

2.多渠道构建工作流：类似于传统的多渠道 APK 构建流程，但将渠道信息替换为空白数据。

3.智能化应用分发：通过自动化触发及响应机制，减少人工干预和错误，提高处理效率。

4.优化 CDN 使用：通过响应头传递偏移量，提升 CDN 文件分发的效率和准确性。

#### 案例化带来的价值
开发平台的支持作用：阿里云提供了低延迟、高并发的函数计算服务，确保在用户上传 APK 文件时能够迅速响应和处理。

简化集成与维护：开发平台提供的自动化工具和函数计算模板，使得集成和维护工作更为轻松，令开发者能将更多精力集中于业务逻辑。

提升用户体验：通过开发平台的自动化、运营监控和日志分析能力，确保了整个文件预处理和分发过程的稳定性及用户体验的提升。

通过该方案，用户能够高效、自动化地完成 .apk 文件的预处理和分发，不仅节省了人力资源，还优化了 CDN 的使用，提升了整体的工作效率和可靠性。借助阿里云的基础设施，开发者能够安心依赖这套解决方案处理高频次、大批量的文件传输需求。

</appdetail>

## 使用流程

<usedetail id="flushContent">

#### 创建应用模版
登录FC控制台创建应用,在通过模版创建应用下,找到对应的模版 apk动态打包,点击立即创建
![](https://img.alicdn.com/imgextra/i3/O1CN015Ju4ps1EjIEw4ymh5_!!6000000000387-0-tps-1266-614.jpg)
#### 参数配置:
根据页面填写需要的参数配置,具体的含义对应参考对应的说明:
![](https://img.alicdn.com/imgextra/i2/O1CN01S4Sl7h1YEsFYkg3uw_!!6000000003028-0-tps-1500-654.jpg)
#### 部署模版
填写完成后点击最下面的创建并部署默认环境:
![](https://img.alicdn.com/imgextra/i2/O1CN011UOQGW1IhEvVuq58Y_!!6000000000924-0-tps-1484-249.jpg)
#### 部署结果:
根据提示创建,等待部署结果:

![](https://img.alicdn.com/imgextra/i2/O1CN01Z7VlKI1YLkBsHJaj9_!!6000000003043-49-tps-750-556.webp)

至此已经完成部署,接下来是按照配置的参数进行验证和使用:

#### 上传apk 母包

在配置的oss存储桶前缀目录中上传测试的apk母包,等待部署的FC应用处理一小会(和母包大小相关),在对应配置的目标桶预处理目标目录下查看对应的预处理后的新文件;具体效果如下

![](https://img.alicdn.com/imgextra/i2/O1CN019ILtCb1wESfjuyR0t_!!6000000006276-0-tps-1504-704.jpg)

</usedetail>

## 注意事项

<matters id="flushContent">

- 建议使用UTF-8或GB 2312编码命名您的文件或文件夹，否则可能会出现解压后的文件或文件夹名称出现乱码、解压过程中断等问题。

</matters>


<devgroup>


## 开发者社区

您如果有关于错误的反馈或者未来的期待，您可以在 [Serverless Devs repo Issues](https://github.com/serverless-devs/serverless-devs/issues) 中进行反馈和交流。如果您想要加入我们的讨论组或者了解 FC 组件的最新动态，您可以通过以下渠道进行：

<p align="center">  

| <img src="https://serverless-article-picture.oss-cn-hangzhou.aliyuncs.com/1635407298906_20211028074819117230.png" width="130px" > | <img src="https://serverless-article-picture.oss-cn-hangzhou.aliyuncs.com/1635407044136_20211028074404326599.png" width="130px" > | <img src="https://serverless-article-picture.oss-cn-hangzhou.aliyuncs.com/1635407252200_20211028074732517533.png" width="130px" > |
| --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| <center>微信公众号：`serverless`</center>                                                                                         | <center>微信小助手：`xiaojiangwh`</center>                                                                                        | <center>钉钉交流群：`33947367`</center>                                                                                           |
</p>
</devgroup>
