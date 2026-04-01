import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// 封装 [FlutterTts]，单例便于多页面复用。
class EchoTtsService {
  EchoTtsService._();

  static final EchoTtsService instance = EchoTtsService._();

  final FlutterTts _tts = FlutterTts();
  bool _inited = false;

  Future<void> ensureInitialized() async {
    if (_inited) return;
    await _tts.setLanguage('en-US');
    if (defaultTargetPlatform == TargetPlatform.iOS) {
      await _tts.setSpeechRate(0.5);
    } else {
      await _tts.setSpeechRate(0.725);
    }
    await _tts.setPitch(1.0);
    await _tts.awaitSpeakCompletion(true);
    _inited = true;
  }

  /// [t]：0~1，映射到各平台可读的语速区间。
  Future<void> setSpeechRateFromSlider(double t) async {
    await ensureInitialized();
    final v = t.clamp(0.0, 1.0);
    if (defaultTargetPlatform == TargetPlatform.iOS) {
      await _tts.setSpeechRate(v);
    } else {
      await _tts.setSpeechRate(0.35 + v * 0.75);
    }
  }

  /// [t]：0~1，映射到约 0.85~1.15 音调。
  Future<void> setPitchFromSlider(double t) async {
    await ensureInitialized();
    final v = t.clamp(0.0, 1.0);
    await _tts.setPitch(0.85 + v * 0.3);
  }

  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    await ensureInitialized();
    await _tts.stop();
    await _tts.speak(text);
  }

  Future<void> stop() async {
    await _tts.stop();
  }
}
