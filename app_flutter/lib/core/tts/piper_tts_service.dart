import 'dart:async';
import 'dart:io';

import 'package:just_audio/just_audio.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:runanywhere/runanywhere.dart';

import '../audio/wav_bytes.dart';
import 'piper_models.dart';

class PiperTtsService {
  PiperTtsService._();

  static final PiperTtsService instance = PiperTtsService._();

  final AudioPlayer _player = AudioPlayer();
  String _voiceId = PiperModels.amyMediumId;
  bool _loadingVoice = false;

  String get voiceId => _voiceId;

  Future<void> setVoice(String voiceId) async {
    _voiceId = voiceId;
    await RunAnywhere.unloadTTSVoice();
  }

  Future<void> ensureVoiceReady({void Function(double progress)? onProgress}) async {
    if (_loadingVoice) return;
    _loadingVoice = true;
    try {
      final downloadedModels = await RunAnywhere.getDownloadedModelsWithInfo();
      final downloaded = downloadedModels.any((m) => m.id == _voiceId);
      if (!downloaded) {
        await for (final p in RunAnywhere.downloadModel(_voiceId)) {
          final total = p.totalBytes;
          final ratio = total <= 0 ? 0.0 : (p.bytesDownloaded / total).clamp(0.0, 1.0);
          onProgress?.call(ratio);
          if (p.state.isCompleted) break;
        }
      }
      await RunAnywhere.loadTTSVoice(_voiceId);
    } finally {
      _loadingVoice = false;
    }
  }

  Future<void> speak(String text) async {
    final t = text.trim();
    if (t.isEmpty) return;

    await ensureVoiceReady();
    final result = await RunAnywhere.synthesize(t, rate: 1.0, pitch: 1.0);

    final wavBytes = float32PcmToWavBytes(result.samples, result.sampleRate);
    final dir = await getTemporaryDirectory();
    final path = p.join(dir.path, 'piper_${DateTime.now().millisecondsSinceEpoch}.wav');
    final f = File(path);
    await f.writeAsBytes(wavBytes, flush: true);
    await _player.setFilePath(path);
    await _player.play();
    unawaited(_player.processingStateStream.firstWhere((s) => s == ProcessingState.completed).then((_) async {
      try {
        await f.delete();
      } catch (_) {}
    }));
  }

  Future<void> stop() => _player.stop();

  Future<void> dispose() async {
    await _player.dispose();
  }
}

