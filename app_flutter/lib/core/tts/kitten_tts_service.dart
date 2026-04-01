import 'dart:async';
import 'dart:developer' show log;
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_kitten_tts/flutter_kitten_tts.dart';
import 'package:just_audio/just_audio.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../audio/wav_bytes.dart';

/// 24 kHz Float32 PCM from [KittenTTS.generate] (package contract).
const kittenTtsSampleRate = 24000;

/// Logcat：与 `flutter` 标签下的 `debugPrint` 一致，便于和 `[ModelManager]` 一起搜。
const kittenTtsLogName = 'MyEnglishChat.TTS';

void _ttsDebug(String message) {
  debugPrint('[$kittenTtsLogName] $message');
}

/// 端侧离线 TTS（KittenML ONNX）。首次初始化会下载模型（约 35MB，缓存在应用支持目录）。
class KittenTtsService {
  KittenTtsService._();

  static final KittenTtsService instance = KittenTtsService._();

  KittenTTS _kitten = KittenTTS();
  final AudioPlayer _player = AudioPlayer();

  /// 见包文档：Bella, Jasper, Luna, Bruno, Rosie, Hugo, Kiki, Leo
  String _voice = 'Jasper';

  Future<void>? _initFuture;

  String get voice => _voice;

  Future<void> setVoice(String voice) async {
    _voice = voice;
  }

  Future<void> ensureInitialized({
    void Function(double progress, String status)? onProgress,
  }) async {
    if (_kitten.isInitialized) return;

    _initFuture ??= _kitten.initialize(
      onProgress: (progress, status) {
        log(
          'init: $status (${(progress * 100).toStringAsFixed(0)}%)',
          name: kittenTtsLogName,
        );
        _ttsDebug('init: $status (${(progress * 100).toStringAsFixed(0)}%)');
        onProgress?.call(progress, status);
      },
    );

    try {
      await _initFuture!;
    } catch (e, st) {
      _initFuture = null;
      _ttsDebug('initialize() FAILED: $e\n$st');
      log(
        'initialize() failed',
        name: kittenTtsLogName,
        error: e,
        stackTrace: st,
      );
      try {
        await _kitten.dispose();
      } catch (e2, st2) {
        _ttsDebug('dispose after failed init: $e2\n$st2');
      }
      _kitten = KittenTTS();
      rethrow;
    }
  }

  Future<void> speak(
    String text, {
    void Function()? onPlaybackComplete,
  }) async {
    final t = text.trim();
    if (t.isEmpty) return;

    try {
      await ensureInitialized();
    } catch (e, st) {
      _ttsDebug('ensureInitialized in speak FAILED: $e\n$st');
      rethrow;
    }

    late Float32List samples;
    try {
      samples = await _kitten.generate(
        t,
        voice: _voice,
        speed: 1.0,
      );
    } catch (e, st) {
      _ttsDebug('generate() FAILED: $e\n$st');
      log('generate() failed', name: kittenTtsLogName, error: e, stackTrace: st);
      rethrow;
    }

    if (samples.isEmpty) {
      const msg = 'KittenTTS returned 0 samples';
      _ttsDebug('$msg — using FlutterTts fallback');
      throw StateError(msg);
    }

    final wavBytes = float32PcmToWavBytes(samples, kittenTtsSampleRate);
    late final File tempFile;
    try {
      final dir = await getTemporaryDirectory();
      final path =
          p.join(dir.path, 'kitten_${DateTime.now().millisecondsSinceEpoch}.wav');
      tempFile = File(path);
      await tempFile.writeAsBytes(wavBytes, flush: true);

      try {
        await _player.setAudioSource(AudioSource.file(path));
        await _player.play();
      } catch (e1, st1) {
        _ttsDebug(
          'playback via file FAILED ($e1), retry data:audio/wav…\n$st1',
        );
        final dataUri = Uri.dataFromBytes(wavBytes, mimeType: 'audio/wav');
        await _player.setAudioSource(AudioSource.uri(dataUri));
        await _player.play();
      }
    } catch (e, st) {
      _ttsDebug('playback FAILED (file + data URI): $e\n$st');
      log('playback failed', name: kittenTtsLogName, error: e, stackTrace: st);
      rethrow;
    }

    _ttsDebug(
      'speak OK: voice=$_voice chars=${t.length} samples=${samples.length}',
    );
    log(
      'speak OK: voice=$_voice chars=${t.length} samples=${samples.length}',
      name: kittenTtsLogName,
    );

    unawaited(
      _player.processingStateStream
          .firstWhere((s) => s == ProcessingState.completed)
          .then((_) async {
        onPlaybackComplete?.call();
        try {
          if (await tempFile.exists()) await tempFile.delete();
        } catch (_) {}
      }),
    );
  }

  Future<void> stop() => _player.stop();

  Future<void> dispose() async {
    await _player.dispose();
    try {
      await _kitten.dispose();
    } catch (_) {}
  }
}
