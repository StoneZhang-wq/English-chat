import 'package:flutter/material.dart';

/// Practice 会话消息与气泡 UI 状态（对齐 Kotlin PracticeMessage / VoiceBubbleUiState）

const kDemoUserTranslation = '（演示译文）This is a placeholder English translation.';
const kDemoAiTranslation = '（演示译文）这是 AI 回复的占位中文翻译。';
const kDemoOptimized =
    '（演示优化）Here\'s a more natural phrasing you could use in conversation.';

const kPronunciationScorePlaceholder = 100;

/// 与 Kotlin PracticeChatGreen 一致
const kPracticeChatGreen = Color(0xFF4CAF50);

abstract final class PracticeChatColors {
  static const textUserBg = Color(0x1E1A1A1A);
  static const textAiBg = Color(0xFFF0F4F8);
  static const voiceBarUserBg = Color(0x1E1A1A1A);
  static const voiceBarAiBg = Color(0xFFF0F4F8);
  static const voiceCardUserBg = Color(0xFFE8F5E9);
  static const voiceCardAiBg = Color(0xFFF0F4F8);
  static const analysisGreen = Color(0xFF4CAF50);
  static const analysisYellow = Color(0xFFFFC107);
  static const analysisOrange = Color(0xFFFF9800);
  static const micRecording = Color(0xFFE53935);
  static const micRecordingCancel = Color(0xFFB71C1C);
  static const recordBarCancel = Color(0xFFC62828);
}

sealed class PracticeMessage {
  final int id;
  final bool isUser;

  const PracticeMessage({required this.id, required this.isUser});
}

final class PracticeTextMessage extends PracticeMessage {
  final String body;

  const PracticeTextMessage({
    required super.id,
    required super.isUser,
    required this.body,
  });
}

final class PracticeVoiceMessage extends PracticeMessage {
  final String? audioPath;
  final int durationMs;
  final String transcript;
  final bool isAiTts;

  const PracticeVoiceMessage({
    required super.id,
    required super.isUser,
    this.audioPath,
    required this.durationMs,
    required this.transcript,
    this.isAiTts = false,
  });

  PracticeVoiceMessage copyWith({
    String? audioPath,
    int? durationMs,
    String? transcript,
    bool? isAiTts,
  }) {
    return PracticeVoiceMessage(
      id: id,
      isUser: isUser,
      audioPath: audioPath ?? this.audioPath,
      durationMs: durationMs ?? this.durationMs,
      transcript: transcript ?? this.transcript,
      isAiTts: isAiTts ?? this.isAiTts,
    );
  }
}

@immutable
class VoiceBubbleUiState {
  final bool expanded;
  final bool translationVisible;
  final String? translatedText;
  final bool optimizedSectionVisible;
  final String? optimizedText;

  const VoiceBubbleUiState({
    this.expanded = false,
    this.translationVisible = false,
    this.translatedText,
    this.optimizedSectionVisible = false,
    this.optimizedText,
  });

  VoiceBubbleUiState copyWith({
    bool? expanded,
    bool? translationVisible,
    String? translatedText,
    bool? optimizedSectionVisible,
    String? optimizedText,
  }) {
    return VoiceBubbleUiState(
      expanded: expanded ?? this.expanded,
      translationVisible: translationVisible ?? this.translationVisible,
      translatedText: translatedText ?? this.translatedText,
      optimizedSectionVisible:
          optimizedSectionVisible ?? this.optimizedSectionVisible,
      optimizedText: optimizedText ?? this.optimizedText,
    );
  }
}

String formatPracticeDurationMs(int ms) {
  final s = (ms.clamp(0, 86400000)) ~/ 1000;
  final m = s ~/ 60;
  final r = s % 60;
  return '$m:${r.toString().padLeft(2, '0')}';
}
