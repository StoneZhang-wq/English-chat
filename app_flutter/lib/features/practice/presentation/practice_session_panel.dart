import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:just_audio/just_audio.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../../../core/theme/echo_theme.dart';
import '../../../data/dto/practice_chat_dto.dart';
import '../../../data/repositories/practice_chat_repository.dart';
import '../domain/practice_chat_models.dart';
import 'practice_message_widgets.dart';

/// 长按低于此毫秒视为短点（与 Kotlin MIC_LONG_PRESS_MS 一致）
const _micLongPressMs = 300;

class PracticeSessionPanel extends StatefulWidget {
  final String scenarioTitle;

  const PracticeSessionPanel({super.key, required this.scenarioTitle});

  @override
  State<PracticeSessionPanel> createState() => _PracticeSessionPanelState();
}

class _PracticeSessionPanelState extends State<PracticeSessionPanel> {
  static const _cancelDragPx = 72.0;

  final _controller = TextEditingController();
  final _listController = ScrollController();
  final AudioRecorder _recorder = AudioRecorder();
  final AudioPlayer _player = AudioPlayer();
  final FlutterTts _tts = FlutterTts();
  final PracticeChatRepository _practiceRepo = PracticeChatRepository();

  final Map<int, VoiceBubbleUiState> _voiceUi = {};
  List<PracticeMessage> _messages = [];

  bool _sending = false;
  bool _transcribing = false;
  bool _recording = false;
  bool _recordCancelHint = false;
  int _recordElapsedSec = 0;
  int? _playingVoiceId;

  Timer? _micHoldTimer;
  Timer? _recordSecTimer;
  StreamSubscription<PlayerState>? _playerSub;

  int? _micPointer;
  double _micAccumulatedDy = 0;
  bool _micDown = false;
  String? _activeRecordPath;
  String? _error;
  String? _micHint;

  bool get _inputBusy => _sending || _transcribing;

  @override
  void initState() {
    super.initState();
    _tts.setCompletionHandler(() {
      if (mounted) setState(() => _playingVoiceId = null);
    });
  }

  @override
  void dispose() {
    _micHoldTimer?.cancel();
    _recordSecTimer?.cancel();
    _playerSub?.cancel();
    unawaited(_recorder.dispose());
    unawaited(_player.dispose());
    unawaited(_tts.stop());
    _controller.dispose();
    _listController.dispose();
    super.dispose();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_listController.hasClients) return;
      final max = _listController.position.maxScrollExtent;
      _listController.animateTo(
        max,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    });
  }

  void _setMicHint(String text) {
    setState(() => _micHint = text);
    Future.delayed(const Duration(seconds: 4), () {
      if (mounted && _micHint == text) setState(() => _micHint = null);
    });
  }

  Future<void> _togglePlayVoice(PracticeVoiceMessage msg) async {
    if (_playingVoiceId == msg.id) {
      await _player.stop();
      await _tts.stop();
      await _playerSub?.cancel();
      _playerSub = null;
      if (mounted) setState(() => _playingVoiceId = null);
      return;
    }

    await _player.stop();
    await _tts.stop();
    await _playerSub?.cancel();
    _playerSub = null;
    if (!mounted) return;
    setState(() => _playingVoiceId = msg.id);

    final useTts = msg.isAiTts ||
        msg.audioPath == null ||
        msg.audioPath!.isEmpty;

    if (useTts) {
      await _tts.speak(msg.transcript);
    } else {
      try {
        await _player.setFilePath(msg.audioPath!);
        await _player.play();
        _playerSub = _player.playerStateStream.listen((s) {
          if (s.processingState == ProcessingState.completed &&
              mounted &&
              _playingVoiceId == msg.id) {
            setState(() => _playingVoiceId = null);
          }
        });
      } catch (_) {
        if (mounted) setState(() => _playingVoiceId = null);
      }
    }
  }

  void _sendTextMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty || _inputBusy || _recording) return;
    final id = DateTime.now().microsecondsSinceEpoch;
    setState(() {
      _messages = [
        ..._messages,
        PracticeTextMessage(id: id, isUser: true, body: text),
      ];
      _controller.clear();
      _error = null;
    });
    _scrollToEnd();
    unawaited(_fetchAssistantReply());
  }

  List<ChatMessageDto> _apiMessagesFromHistory() {
    return _messages.map((m) {
      switch (m) {
        case PracticeTextMessage t:
          return ChatMessageDto(
            role: t.isUser ? 'user' : 'assistant',
            content: t.body,
          );
        case PracticeVoiceMessage v:
          final c = v.transcript.trim();
          final content =
              (c.isEmpty || c == '转写中…') ? '[语音消息]' : c;
          return ChatMessageDto(
            role: v.isUser ? 'user' : 'assistant',
            content: content,
          );
      }
    }).toList();
  }

  /// 将当前 `_messages` 整段发给 backend LLM，回复以 AI 语音气泡（TTS）展示（与 Kotlin 一致）
  Future<void> _fetchAssistantReply() async {
    if (!mounted) return;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final reply = await _practiceRepo.sendChat(
        messages: _apiMessagesFromHistory(),
        scenarioTitle: widget.scenarioTitle.trim().isEmpty
            ? null
            : widget.scenarioTitle.trim(),
      );
      final trimmed = reply.trim();
      if (trimmed.isEmpty) {
        throw Exception('模型返回为空');
      }
      if (!mounted) return;
      final aid = DateTime.now().microsecondsSinceEpoch;
      final durMs = (trimmed.length * 60).clamp(1500, 120000).toInt();
      setState(() {
        _messages = [
          ..._messages,
          PracticeVoiceMessage(
            id: aid,
            isUser: false,
            audioPath: null,
            durationMs: durMs,
            transcript: trimmed,
            isAiTts: true,
          ),
        ];
        _voiceUi[aid] = const VoiceBubbleUiState();
      });
      _scrollToEnd();
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e is Exception ? '$e' : '请求失败：$e';
        });
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _startRecording() async {
    if (await _recorder.isRecording()) return;

    if (!await _recorder.hasPermission()) {
      if (mounted) {
        setState(() => _error = '需要麦克风权限才能使用语音输入');
      }
      return;
    }

    final dir = await getTemporaryDirectory();
    _activeRecordPath = p.join(
      dir.path,
      'practice_${DateTime.now().millisecondsSinceEpoch}.wav',
    );

    try {
      await _recorder.start(
        const RecordConfig(encoder: AudioEncoder.wav),
        path: _activeRecordPath!,
      );
      if (!mounted) return;
      setState(() {
        _recording = true;
        _recordCancelHint = false;
        _recordElapsedSec = 0;
        _error = null;
      });
      _recordSecTimer?.cancel();
      _recordSecTimer = Timer.periodic(const Duration(seconds: 1), (_) {
        if (mounted && _recording) setState(() => _recordElapsedSec++);
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _recording = false;
          _error = '无法开始录音：$e';
        });
      }
    }
  }

  Future<void> _cancelRecording() async {
    _recordSecTimer?.cancel();
    if (await _recorder.isRecording()) {
      final path = await _recorder.stop();
      if (path != null && path.isNotEmpty) {
        try {
          await File(path).delete();
        } catch (_) {}
      }
    }
    if (mounted) {
      setState(() {
        _recording = false;
        _recordCancelHint = false;
      });
    }
  }

  Future<void> _stopRecordingAndSend() async {
    _recordSecTimer?.cancel();
    String? path;
    if (await _recorder.isRecording()) {
      path = await _recorder.stop();
    }

    if (!mounted) return;
    setState(() {
      _recording = false;
      _recordCancelHint = false;
    });

    if (path == null || path.isEmpty) {
      setState(() => _error = '录音过短或失败');
      return;
    }

    final id = DateTime.now().microsecondsSinceEpoch;
    final durationMs = (_recordElapsedSec * 1000 + 400).clamp(400, 600000);

    setState(() {
      _messages = [
        ..._messages,
        PracticeVoiceMessage(
          id: id,
          isUser: true,
          audioPath: path,
          durationMs: durationMs,
          transcript: '转写中…',
        ),
      ];
      _voiceUi[id] = const VoiceBubbleUiState();
      _error = null;
    });
    _scrollToEnd();

    if (!mounted) return;
    setState(() => _transcribing = true);
    await Future.delayed(const Duration(milliseconds: 900));
    if (!mounted) return;
    setState(() {
      _transcribing = false;
      _messages = _messages.map((m) {
        if (m is PracticeVoiceMessage && m.id == id) {
          return m.copyWith(
            transcript:
                '（占位）模拟英文转写：I would like to practice speaking in this scenario.',
          );
        }
        return m;
      }).toList();
    });
    unawaited(_fetchAssistantReply());
  }

  void _onMicPointerDown(PointerDownEvent e) {
    if (_inputBusy) return;
    _micPointer = e.pointer;
    _micAccumulatedDy = 0;
    _micDown = true;
    _micHoldTimer?.cancel();
    _micHoldTimer = Timer(const Duration(milliseconds: _micLongPressMs), () {
      if (!_micDown || !mounted || _inputBusy) return;
      unawaited(_startRecording());
    });
  }

  void _onMicPointerMove(PointerMoveEvent e) {
    if (e.pointer != _micPointer) return;
    _micAccumulatedDy += e.delta.dy;
    if (_recording) {
      final cancel = _micAccumulatedDy < -_cancelDragPx;
      if (cancel != _recordCancelHint) {
        setState(() => _recordCancelHint = cancel);
      }
    }
  }

  void _onMicPointerUp(PointerUpEvent e) {
    if (e.pointer != _micPointer) return;
    _micHoldTimer?.cancel();
    _micDown = false;
    _micPointer = null;

    if (!_recording) {
      _setMicHint('长按麦克风说话，松手发送语音；上滑取消。');
      return;
    }

    if (_recordCancelHint) {
      unawaited(_cancelRecording());
    } else {
      unawaited(_stopRecordingAndSend());
    }
  }

  void _onMicPointerCancel(PointerCancelEvent e) {
    if (e.pointer != _micPointer) return;
    _micHoldTimer?.cancel();
    _micDown = false;
    _micPointer = null;
    if (_recording) unawaited(_cancelRecording());
  }

  Widget _buildMessage(PracticeMessage msg) {
    switch (msg) {
      case PracticeTextMessage():
        return PracticeTextBubble(msg: msg);
      case PracticeVoiceMessage():
        final st = _voiceUi[msg.id] ?? const VoiceBubbleUiState();
        return PracticeVoiceBubble(
          msg: msg,
          state: st,
          isPlaying: _playingVoiceId == msg.id,
          onPlay: () => unawaited(_togglePlayVoice(msg)),
          onToggleExpand: () {
            setState(() {
              final cur = _voiceUi[msg.id] ?? const VoiceBubbleUiState();
              _voiceUi[msg.id] = cur.copyWith(expanded: !cur.expanded);
            });
          },
          onToggleTranslate: () {
            setState(() {
              final cur = _voiceUi[msg.id] ?? const VoiceBubbleUiState();
              final show = !cur.translationVisible;
              _voiceUi[msg.id] = cur.copyWith(
                translationVisible: show,
                translatedText: show
                    ? (cur.translatedText ??
                        (msg.isUser ? kDemoUserTranslation : kDemoAiTranslation))
                    : cur.translatedText,
              );
            });
          },
          onToggleOptimize: () {
            setState(() {
              final cur = _voiceUi[msg.id] ?? const VoiceBubbleUiState();
              final show = !cur.optimizedSectionVisible;
              _voiceUi[msg.id] = cur.copyWith(
                optimizedSectionVisible: show,
                optimizedText: show
                    ? (cur.optimizedText ?? kDemoOptimized)
                    : cur.optimizedText,
              );
            });
          },
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final canSendText = _controller.text.trim().isNotEmpty &&
        !_inputBusy &&
        !_recording;
    final micBg = !_recording
        ? kPracticeChatGreen
        : _recordCancelHint
            ? PracticeChatColors.micRecordingCancel
            : PracticeChatColors.micRecording;
    final micRing =
        _recording ? Colors.white.withValues(alpha: 0.45) : Colors.transparent;

    return Column(
      children: [
        _TaskBanner(scenarioTitle: widget.scenarioTitle),
        const SizedBox(height: 12),
        Expanded(
          child: Stack(
            children: [
              Container(
                decoration: BoxDecoration(
                  color: echoSurface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: echoBorder),
                ),
                clipBehavior: Clip.antiAlias,
                child: _messages.isEmpty && !_sending
                    ? Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          '输入文字后点键盘「发送」；或长按右侧黑色麦克风说话，松手发送、上滑取消。',
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: echoMuted),
                        ),
                      )
                    : ListView.builder(
                        controller: _listController,
                        padding: const EdgeInsets.all(12),
                        itemCount: _messages.length,
                        itemBuilder: (context, i) {
                          final msg = _messages[i];
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: KeyedSubtree(
                              key: ValueKey(msg.id),
                              child: _buildMessage(msg),
                            ),
                          );
                        },
                      ),
              ),
              if (_sending && _messages.isNotEmpty)
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 8,
                  child: Center(
                    child: SizedBox(
                      width: 28,
                      height: 28,
                      child: CircularProgressIndicator(
                        strokeWidth: 3,
                        color: echoOnBackground.withValues(alpha: 0.6),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: 8),
          Text(
            _error!,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: Theme.of(context).colorScheme.error),
          ),
        ],
        const SizedBox(height: 10),
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_transcribing && !_recording)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  '正在识别语音…',
                  textAlign: TextAlign.center,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: echoMuted),
                ),
              ),
            if (_recording)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  _recordCancelHint ? '松开手指，取消发送' : '松开发送，上滑取消',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: _recordCancelHint
                            ? Theme.of(context).colorScheme.error
                            : echoOnBackground.withValues(alpha: 0.65),
                      ),
                ),
              ),
            Row(
              children: [
                Material(
                  color: echoSurface,
                  borderRadius: BorderRadius.circular(20),
                  child: InkWell(
                    onTap: () => _setMicHint('提示内容生成将在后续版本开放'),
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding:
                          const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: kPracticeChatGreen.withValues(alpha: 0.45),
                        ),
                      ),
                      child: Icon(
                        Icons.lightbulb,
                        size: 22,
                        color: kPracticeChatGreen,
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Listener(
                  behavior: HitTestBehavior.opaque,
                  onPointerDown: _onMicPointerDown,
                  onPointerMove: _onMicPointerMove,
                  onPointerUp: _onMicPointerUp,
                  onPointerCancel: _onMicPointerCancel,
                  child: SizedBox(
                    width: 48,
                    height: 48,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        Container(
                          decoration: BoxDecoration(
                            color: micBg,
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(color: micRing, width: 2),
                          ),
                        ),
                        const Icon(Icons.mic, color: Colors.white, size: 24),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                if (_recording) ...[
                  Expanded(
                    child: Container(
                      constraints: const BoxConstraints(minHeight: 48),
                      decoration: BoxDecoration(
                        color: _recordCancelHint
                            ? PracticeChatColors.recordBarCancel
                            : kPracticeChatGreen,
                        borderRadius: BorderRadius.circular(24),
                      ),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          WaveformMini(
                            barColor: Colors.white.withValues(alpha: 0.9),
                          ),
                          Text(
                            '${_recordElapsedSec.clamp(0, 999)}s',
                            style: Theme.of(context)
                                .textTheme
                                .labelLarge
                                ?.copyWith(color: Colors.white),
                          ),
                        ],
                      ),
                    ),
                  ),
                ] else ...[
                  Expanded(
                    child: Container(
                      constraints: const BoxConstraints(minHeight: 48),
                      decoration: BoxDecoration(
                        color: echoSurface,
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: echoBorder.withValues(alpha: 0.35),
                        ),
                      ),
                      child: TextField(
                        controller: _controller,
                        minLines: 1,
                        maxLines: 4,
                        enabled: !_inputBusy,
                        onChanged: (_) => setState(() {}),
                        style: Theme.of(context)
                            .textTheme
                            .bodyMedium
                            ?.copyWith(color: echoOnBackground),
                        decoration: InputDecoration(
                          hintText: '对话',
                          hintStyle: Theme.of(context)
                              .textTheme
                              .bodyMedium
                              ?.copyWith(color: echoMuted),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 14,
                          ),
                        ),
                        textInputAction: TextInputAction.send,
                        onSubmitted: (_) => _sendTextMessage(),
                      ),
                    ),
                  ),
                ],
                const SizedBox(width: 10),
                Material(
                  color: canSendText
                      ? kPracticeChatGreen
                      : echoMuted.withValues(alpha: 0.35),
                  borderRadius: BorderRadius.circular(24),
                  child: InkWell(
                    onTap: canSendText ? _sendTextMessage : null,
                    borderRadius: BorderRadius.circular(24),
                    child: const SizedBox(
                      width: 48,
                      height: 48,
                      child: Icon(Icons.send, color: Colors.white, size: 24),
                    ),
                  ),
                ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Text(
                '内容由 AI 生成',
                textAlign: TextAlign.center,
                style: Theme.of(context)
                    .textTheme
                    .labelSmall
                    ?.copyWith(color: echoMuted),
              ),
            ),
            if (_micHint != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  _micHint!,
                  style: Theme.of(context)
                      .textTheme
                      .labelSmall
                      ?.copyWith(color: echoMuted),
                ),
              ),
          ],
        ),
      ],
    );
  }
}

class _TaskBanner extends StatelessWidget {
  final String scenarioTitle;

  const _TaskBanner({required this.scenarioTitle});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: echoTaskYellow,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: echoTaskYellowBorder),
      ),
      child: Row(
        children: [
          Text(
            'CURRENT TASK:',
            style: Theme.of(context)
                .textTheme
                .labelSmall
                ?.copyWith(color: echoMuted),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              scenarioTitle.isEmpty ? 'Practice in this scenario.' : scenarioTitle,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}
