import 'dart:async';

import 'package:flutter/foundation.dart' show defaultTargetPlatform, TargetPlatform;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../core/audio/echo_tts_service.dart';
import '../../../core/audio/vosk_platform.dart';
import '../../../core/audio/vosk_speech_controller.dart';
import '../../../core/theme/echo_theme.dart';

/// 与 [ModelLoader] / pubspec 中声明的路径一致。
const String kVoskModelAssetZip = 'assets/models/vosk-model-small-en-us-0.15.zip';

/// 离线 STT（Vosk [vosk_flutter_service]，Android/iOS 麦克风流）+ TTS（flutter_tts）体验页。
class VoiceLabScreen extends StatefulWidget {
  const VoiceLabScreen({super.key});

  @override
  State<VoiceLabScreen> createState() => _VoiceLabScreenState();
}

class _VoiceLabScreenState extends State<VoiceLabScreen>
    with SingleTickerProviderStateMixin {
  final _recognitionController = TextEditingController();
  final _ttsController = TextEditingController(
    text: 'Hello, this is a sample sentence for text-to-speech.',
  );

  VoskSpeechController? _vosk;
  bool _modelLoading = false;
  String? _modelError;
  bool _recording = false;

  String _finalAsrBuffer = '';
  String _livePartial = '';

  double _ttsRateSlider = 0.5;
  double _ttsPitchSlider = 0.5;

  late final AnimationController _pulse;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    await EchoTtsService.instance.ensureInitialized();
    await EchoTtsService.instance.setSpeechRateFromSlider(_ttsRateSlider);
    await EchoTtsService.instance.setPitchFromSlider(_ttsPitchSlider);
    if (!mounted) return;
    if (isVoskMicStreamingSupported) {
      await _loadVoskModel();
    }
  }

  Future<void> _loadVoskModel() async {
    setState(() {
      _modelLoading = true;
      _modelError = null;
    });
    try {
      await rootBundle.load(kVoskModelAssetZip);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _modelLoading = false;
        _modelError =
            '未在资源中找到 $kVoskModelAssetZip。请从 Alphacep 下载英文小包并放入 assets/models/，'
            '详见该目录下说明。';
      });
      return;
    }

    VoskSpeechController? c;
    try {
      c = VoskSpeechController(
        onPartial: _onAsrPartial,
        onFinal: _onAsrFinal,
        onError: (e, st) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('识别错误: $e')),
            );
          }
        },
      );
      final path = await VoskSpeechController.loadModelFromAssets(kVoskModelAssetZip);
      await c.initEngine(path);
      if (!mounted) {
        await c.dispose();
        return;
      }
      setState(() {
        _vosk = c;
        _modelLoading = false;
      });
    } catch (e) {
      await c?.dispose();
      if (!mounted) return;
      setState(() {
        _modelLoading = false;
        _modelError = '模型初始化失败: $e';
      });
    }
  }

  void _onAsrPartial(String t) {
    if (!mounted) return;
    setState(() => _livePartial = t);
    _syncRecognitionText();
  }

  void _onAsrFinal(String t) {
    if (!mounted) return;
    setState(() {
      final trimmed = t.trim();
      if (trimmed.isEmpty) return;
      if (_finalAsrBuffer.isEmpty) {
        _finalAsrBuffer = trimmed;
      } else {
        _finalAsrBuffer = '$_finalAsrBuffer $trimmed';
      }
      _livePartial = '';
    });
    _syncRecognitionText();
  }

  void _syncRecognitionText() {
    final display = _livePartial.isEmpty
        ? _finalAsrBuffer
        : _finalAsrBuffer.isEmpty
            ? _livePartial
            : '$_finalAsrBuffer $_livePartial';
    _recognitionController.value = TextEditingValue(
      text: display,
      selection: TextSelection.collapsed(offset: display.length),
    );
  }

  Future<void> _toggleRecording() async {
    if (!isVoskMicStreamingSupported) return;
    if (_vosk == null || !_vosk!.isEngineReady) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('模型未就绪，无法录音')),
      );
      return;
    }
    if (_recording) {
      await _vosk!.stop();
      setState(() => _recording = false);
      _pulse.stop();
      _pulse.reset();
      return;
    }

    setState(() {
      _finalAsrBuffer = '';
      _livePartial = '';
    });
    _recognitionController.clear();

    final mic = await Permission.microphone.request();
    if (!mic.isGranted) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('需要麦克风权限才能进行离线识别')),
      );
      return;
    }

    setState(() => _recording = true);
    _pulse.repeat(reverse: true);
    try {
      await _vosk!.start();
    } catch (e) {
      if (!mounted) return;
      setState(() => _recording = false);
      _pulse.stop();
      _pulse.reset();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('无法开始录音: $e')),
      );
    }
  }

  Future<void> _speak() async {
    final text = _ttsController.text.trim();
    if (text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请输入要朗读的英文')),
      );
      return;
    }
    await EchoTtsService.instance.speak(text);
  }

  @override
  void dispose() {
    _pulse.dispose();
    _recognitionController.dispose();
    _ttsController.dispose();
    unawaited(_vosk?.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Voice Lab'),
      ),
      body: Column(
        children: [
          if (defaultTargetPlatform == TargetPlatform.iOS)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Card(
                color: echoTaskYellow,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(
                    'iOS：首次在本机构建前，请在项目根目录执行 '
                    'dart run vosk_flutter_service install -t ios '
                    '以下载 Vosk 原生库（详见 assets/models/README.txt）。',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ),
            ),
          if (!isVoskMicStreamingSupported)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Card(
                color: echoTaskYellow,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(
                    '当前平台不支持 Vosk 麦克风流；可使用下方朗读（TTS）。',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ),
            ),
          if (_modelLoading)
            const LinearProgressIndicator(minHeight: 3),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    '识别文本（可编辑）',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  if (_modelError != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        _modelError!,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).colorScheme.error,
                            ),
                      ),
                    ),
                  Expanded(
                    flex: 3,
                    child: TextField(
                      controller: _recognitionController,
                      maxLines: null,
                      expands: true,
                      textAlignVertical: TextAlignVertical.top,
                      decoration: InputDecoration(
                        alignLabelWithHint: true,
                        hintText: isVoskMicStreamingSupported
                            ? '录音时实时显示识别；也可手动修改'
                            : '当前平台无 Vosk 流式识别',
                        border: const OutlineInputBorder(),
                        filled: true,
                        fillColor: echoSurface,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Divider(),
                  const SizedBox(height: 8),
                  Text(
                    '朗读',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _ttsController,
                    minLines: 2,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      hintText: '输入英文句子…',
                      border: OutlineInputBorder(),
                      filled: true,
                      fillColor: echoSurface,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '语速',
                              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                    color: echoMuted,
                                  ),
                            ),
                            Slider(
                              value: _ttsRateSlider,
                              onChanged: (v) async {
                                setState(() => _ttsRateSlider = v);
                                await EchoTtsService.instance
                                    .setSpeechRateFromSlider(v);
                              },
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '音调',
                              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                    color: echoMuted,
                                  ),
                            ),
                            Slider(
                              value: _ttsPitchSlider,
                              onChanged: (v) async {
                                setState(() => _ttsPitchSlider = v);
                                await EchoTtsService.instance.setPitchFromSlider(v);
                              },
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  FilledButton.icon(
                    onPressed: _speak,
                    icon: const Icon(Icons.volume_up_outlined),
                    label: const Text('朗读'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: isVoskMicStreamingSupported
          ? ScaleTransition(
              scale: Tween<double>(begin: 1, end: 1.12).animate(
                CurvedAnimation(parent: _pulse, curve: Curves.easeInOut),
              ),
              child: FloatingActionButton(
                onPressed: _modelLoading || _vosk == null ? null : _toggleRecording,
                backgroundColor: _recording
                    ? Theme.of(context).colorScheme.error
                    : Theme.of(context).colorScheme.primary,
                foregroundColor: _recording
                    ? Theme.of(context).colorScheme.onError
                    : Theme.of(context).colorScheme.onPrimary,
                child: Icon(_recording ? Icons.stop : Icons.mic),
              ),
            )
          : null,
    );
  }
}
