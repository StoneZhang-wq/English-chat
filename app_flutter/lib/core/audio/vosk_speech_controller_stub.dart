/// Web 等无 `dart:io` 的目标：不加载 Vosk FFI，仅提供与 [VoskSpeechController] 相同的类型占位。
class VoskSpeechController {
  VoskSpeechController({
    required this.onPartial,
    required this.onFinal,
    required this.onError,
  });

  final void Function(String text) onPartial;
  final void Function(String text) onFinal;
  final void Function(Object error, StackTrace stack) onError;

  bool get isEngineReady => false;

  static Future<String> loadModelFromAssets(String assetZipPath) async {
    throw UnsupportedError('Vosk 离线 STT 在 Web 上不可用（请使用 Android / iOS / 桌面）。');
  }

  Future<void> initEngine(String modelDirPath) async {
    throw UnsupportedError('Vosk 离线 STT 在 Web 上不可用（请使用 Android / iOS / 桌面）。');
  }

  Future<void> start() async {
    throw StateError('Vosk 未初始化');
  }

  Future<void> stop() async {}

  Future<void> dispose() async {}
}
