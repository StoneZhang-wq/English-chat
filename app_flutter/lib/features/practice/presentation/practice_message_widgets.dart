import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/practice_chat_models.dart';

class WaveformMini extends StatelessWidget {
  final Color barColor;

  const WaveformMini({super.key, required this.barColor});

  static final _heights = [6.0, 12.0, 8.0, 14.0, 10.0, 16.0, 9.0, 13.0, 7.0, 11.0];

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        for (var i = 0; i < _heights.length; i++) ...[
          if (i > 0) const SizedBox(width: 2),
          Container(
            width: 3,
            height: _heights[i],
            decoration: BoxDecoration(
              color: barColor,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ],
      ],
    );
  }
}

class PracticeTextBubble extends StatelessWidget {
  final PracticeTextMessage msg;

  const PracticeTextBubble({super.key, required this.msg});

  @override
  Widget build(BuildContext context) {
    final align = msg.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final bg = msg.isUser ? PracticeChatColors.textUserBg : PracticeChatColors.textAiBg;

    return Column(
      crossAxisAlignment: align,
      children: [
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 300),
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: bg,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Text(
                msg.body,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: echoOnBackground,
                    ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class PracticeVoiceBubble extends StatelessWidget {
  final PracticeVoiceMessage msg;
  final VoiceBubbleUiState state;
  final bool isPlaying;
  final VoidCallback onPlay;
  final VoidCallback onToggleExpand;
  final VoidCallback onToggleTranslate;
  final VoidCallback onToggleOptimize;

  const PracticeVoiceBubble({
    super.key,
    required this.msg,
    required this.state,
    required this.isPlaying,
    required this.onPlay,
    required this.onToggleExpand,
    required this.onToggleTranslate,
    required this.onToggleOptimize,
  });

  @override
  Widget build(BuildContext context) {
    final align = msg.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final barBg = msg.isUser ? PracticeChatColors.voiceBarUserBg : PracticeChatColors.voiceBarAiBg;
    final cardBg =
        msg.isUser ? PracticeChatColors.voiceCardUserBg : PracticeChatColors.voiceCardAiBg;

    return Column(
      crossAxisAlignment: align,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            IconButton(
              onPressed: onPlay,
              iconSize: 22,
              constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
              padding: EdgeInsets.zero,
              icon: Icon(
                Icons.play_arrow,
                size: 22,
                color: isPlaying ? echoOnBackground : echoMuted,
              ),
            ),
            const SizedBox(width: 2),
            Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: onToggleExpand,
                borderRadius: BorderRadius.circular(12),
                child: Ink(
                  decoration: BoxDecoration(
                    color: barBg,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        WaveformMini(
                          barColor: echoMuted.withValues(alpha: 0.5),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          formatPracticeDurationMs(msg.durationMs),
                          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                                color: echoMuted,
                              ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
        if (!state.expanded)
          Padding(
            padding: const EdgeInsets.only(top: 4, left: 4, right: 4),
            child: Text(
              '点击语音条查看英文',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: echoMuted),
            ),
          )
        else ...[
          const SizedBox(height: 6),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 300),
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: echoBorder.withValues(alpha: 0.35)),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                child: msg.isUser
                    ? _UserExpandedBody(
                        msg: msg,
                        state: state,
                        isPlaying: isPlaying,
                        onPlay: onPlay,
                        onToggleTranslate: onToggleTranslate,
                        onToggleOptimize: onToggleOptimize,
                      )
                    : _AiExpandedBody(
                        msg: msg,
                        state: state,
                        isPlaying: isPlaying,
                        onPlay: onPlay,
                        onToggleTranslate: onToggleTranslate,
                      ),
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _UserExpandedBody extends StatelessWidget {
  final PracticeVoiceMessage msg;
  final VoiceBubbleUiState state;
  final bool isPlaying;
  final VoidCallback onPlay;
  final VoidCallback onToggleTranslate;
  final VoidCallback onToggleOptimize;

  const _UserExpandedBody({
    required this.msg,
    required this.state,
    required this.isPlaying,
    required this.onPlay,
    required this.onToggleTranslate,
    required this.onToggleOptimize,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(
                msg.transcript,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: echoOnBackground,
                    ),
              ),
            ),
            IconButton(
              onPressed: onPlay,
              iconSize: 22,
              constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
              padding: EdgeInsets.zero,
              icon: Icon(
                Icons.play_arrow,
                color: isPlaying ? PracticeChatColors.analysisGreen : echoMuted,
                size: 22,
              ),
            ),
          ],
        ),
        if (state.translationVisible && state.translatedText != null) ...[
          const SizedBox(height: 8),
          Text(
            state.translatedText!,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: echoOnBackground,
                ),
          ),
        ],
        Divider(height: 20, color: echoBorder.withValues(alpha: 0.4)),
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            IconButton(
              onPressed: onToggleTranslate,
              iconSize: 22,
              constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
              padding: EdgeInsets.zero,
              icon: Icon(
                Icons.translate,
                color: state.translationVisible
                    ? PracticeChatColors.analysisGreen
                    : echoMuted,
                size: 22,
              ),
            ),
            Expanded(
              child: Center(
                child: InkWell(
                  onTap: onToggleOptimize,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '优化表达',
                          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                                color: echoOnBackground,
                              ),
                        ),
                        const SizedBox(width: 2),
                        Icon(
                          state.optimizedSectionVisible
                              ? Icons.expand_less_outlined
                              : Icons.expand_more_outlined,
                          size: 18,
                          color: echoMuted,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: _ScoreChipsRow(),
            ),
          ],
        ),
        if (state.optimizedSectionVisible && state.optimizedText != null) ...[
          const SizedBox(height: 10),
          Text(
            state.optimizedText!,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: echoOnBackground,
                ),
          ),
        ],
      ],
    );
  }
}

class _ScoreChipsRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text('语法', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: echoMuted)),
        const SizedBox(width: 2),
        Icon(Icons.thumb_up, size: 14, color: PracticeChatColors.analysisGreen),
        Container(
          width: 1,
          height: 16,
          margin: const EdgeInsets.symmetric(horizontal: 4),
          color: echoBorder.withValues(alpha: 0.5),
        ),
        Text('用词', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: echoMuted)),
        const SizedBox(width: 2),
        Icon(Icons.thumb_up, size: 14, color: PracticeChatColors.analysisYellow),
        Container(
          width: 1,
          height: 16,
          margin: const EdgeInsets.symmetric(horizontal: 4),
          color: echoBorder.withValues(alpha: 0.5),
        ),
        Text('发音', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: echoMuted)),
        const SizedBox(width: 2),
        Text(
          '$kPronunciationScorePlaceholder',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: PracticeChatColors.analysisOrange,
              ),
        ),
      ],
    );
  }
}

class _AiExpandedBody extends StatelessWidget {
  final PracticeVoiceMessage msg;
  final VoiceBubbleUiState state;
  final bool isPlaying;
  final VoidCallback onPlay;
  final VoidCallback onToggleTranslate;

  const _AiExpandedBody({
    required this.msg,
    required this.state,
    required this.isPlaying,
    required this.onPlay,
    required this.onToggleTranslate,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                msg.transcript,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: echoOnBackground,
                    ),
              ),
            ),
            IconButton(
              onPressed: onPlay,
              iconSize: 22,
              constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
              padding: EdgeInsets.zero,
              icon: Icon(
                Icons.play_arrow,
                color: isPlaying ? PracticeChatColors.analysisGreen : echoMuted,
                size: 22,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        IconButton(
          onPressed: onToggleTranslate,
          iconSize: 22,
          constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
          padding: EdgeInsets.zero,
          icon: Icon(
            Icons.translate,
            color: state.translationVisible ? PracticeChatColors.analysisGreen : echoMuted,
            size: 22,
          ),
        ),
        if (state.translationVisible && state.translatedText != null) ...[
          const SizedBox(height: 6),
          Text(
            state.translatedText!,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: echoOnBackground,
                ),
          ),
        ],
      ],
    );
  }
}
