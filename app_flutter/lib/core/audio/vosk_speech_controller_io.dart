import 'dart:async';

import 'package:vosk_flutter_service/vosk_flutter.dart';

import 'vosk_json_parser.dart';
import 'vosk_platform.dart';

/// 封装 [SpeechService] 的麦克风流式识别（16 kHz，与 Vosk 推荐一致）。
///
/// 须在支持平台上先 [loadModelFromAssets]，再 [initEngine]，再 [start] / [stop]。
class VoskSpeechController {
  VoskSpeechController({
    required this.onPartial,
    required this.onFinal,
    required this.onError,
  });

  final void Function(String text) onPartial;
  final void Function(String text) onFinal;
  final void Function(Object error, StackTrace stack) onError;

  Model? _model;
  Recognizer? _recognizer;
  SpeechService? _speech;
  StreamSubscription<String>? _partialSub;
  StreamSubscription<String>? _resultSub;
  bool _listenersAttached = false;

  bool get isEngineReady => _speech != null;

  /// 解压到应用文档目录 `.../models/`，第二次起若目录已存在则跳过解压（由 [ModelLoader] 处理）。
  static Future<String> loadModelFromAssets(String assetZipPath) async {
    if (!isVoskMicStreamingSupported) {
      throw UnsupportedError('Vosk 麦克风流仅支持 Android / iOS');
    }
    final loader = ModelLoader();
    return loader.loadFromAssets(assetZipPath);
  }

  Future<void> initEngine(String modelDirPath) async {
    if (!isVoskMicStreamingSupported) {
      throw UnsupportedError('Vosk 麦克风流仅支持 Android / iOS');
    }
    await dispose();
    final vosk = VoskFlutterPlugin.instance();
    _model = await vosk.createModel(modelDirPath);
    _recognizer = await vosk.createRecognizer(
      model: _model!,
      sampleRate: 16000,
    );
    try {
      _speech = await vosk.initSpeechService(_recognizer!);
    } on MicrophoneAccessDeniedException catch (e, st) {
      onError(e, st);
      rethrow;
    }
  }

  void _attachListenersOnce() {
    if (_listenersAttached || _speech == null) return;
    _listenersAttached = true;
    _partialSub = _speech!.onPartial().listen(
      (raw) {
        final t = extractVoskDisplayText(raw);
        if (t.isNotEmpty) onPartial(t);
      },
      onError: (e, st) => onError(e, st ?? StackTrace.current),
    );
    _resultSub = _speech!.onResult().listen(
      (raw) {
        final t = extractVoskDisplayText(raw);
        if (t.isNotEmpty) onFinal(t);
      },
      onError: (e, st) => onError(e, st ?? StackTrace.current),
    );
  }

  Future<void> start() async {
    if (_speech == null) {
      throw StateError('Vosk 未初始化');
    }
    _attachListenersOnce();
    await _speech!.start();
  }

  Future<void> stop() async {
    await _speech?.stop();
    await _recognizer?.reset();
  }

  Future<void> dispose() async {
    await _partialSub?.cancel();
    await _resultSub?.cancel();
    _partialSub = null;
    _resultSub = null;
    _listenersAttached = false;
    try {
      await _speech?.dispose();
    } catch (_) {}
    _speech = null;
    try {
      await _recognizer?.dispose();
    } catch (_) {}
    _recognizer = null;
    try {
      _model?.dispose();
    } catch (_) {}
    _model = null;
  }
}
