Vosk 英文小包（离线语音识别）
================================

依赖插件：vosk_flutter_service（支持 Android / iOS）。

1. 下载模型
   打开 https://alphacephei.com/vosk/models
   下载「vosk-model-small-en-us-0.15」对应的 .zip（约 40MB）。

2. 放置
   将 zip 文件**原文件名**放到本目录：
   vosk-model-small-en-us-0.15.zip

3. iOS / macOS 原生库（插件要求）
   在 app_flutter 项目根目录执行（按目标平台选一）：
   dart run vosk_flutter_service install -t ios
   dart run vosk_flutter_service install -t macos
   Android 自带原生库，一般无需此步骤。

4. 构建
   在项目根目录执行 flutter pub get，再运行或打包应用。

说明：模型较大，通常勿提交到 Git；协作者各自下载后放入此目录。
