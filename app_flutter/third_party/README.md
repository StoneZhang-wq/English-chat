# third_party / vosk_flutter_service

来自 pub.dev `vosk_flutter_service` **0.1.0** 的副本，仅修改 `pubspec.yaml`：**移除 Web 平台注册**。

原因：上游 `web.fileName` 写成 `lib/src/...`，导致生成错误的 `import`；且主库在 Web 上会拉入 FFI 桩，无法通过编译。

应用侧对 Web 使用 `lib/core/audio/vosk_speech_controller_stub.dart`（条件导入），Chrome 上可正常跑 UI 与 TTS；离线 STT 仍仅在 Android / iOS 可用。

若需从本机 pub 缓存重新生成副本，可在仓库根执行（路径按本机调整）：

`robocopy "%LOCALAPPDATA%\Pub\Cache\hosted\pub.dev\vosk_flutter_service-0.1.0" "app_flutter\third_party\vosk_flutter_service" /E`

然后重新应用对 `pubspec.yaml` 的 Web 段删除。
