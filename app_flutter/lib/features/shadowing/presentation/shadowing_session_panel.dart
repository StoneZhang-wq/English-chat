import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';

class ShadowingSessionPanel extends StatelessWidget {
  const ShadowingSessionPanel({super.key});

  @override
  Widget build(BuildContext context) {
    final dialogueLines = const [
      'Hello, I have a reservation under the name Smith for three nights.',
      'Good evening, Mr. Smith. May I see your ID and credit card for incidentals?',
    ];

    return SingleChildScrollView(
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: echoSurface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: echoBorder),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _DialogueLine(speaker: 'SPEAKER A', text: dialogueLines[0]),
                const SizedBox(height: 16),
                _DialogueLine(speaker: 'SPEAKER B', text: dialogueLines[1]),
                const SizedBox(height: 20),
                Container(
                  height: 90,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: echoBackground,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: echoBorder),
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    'Waveform（占位）',
                    style: Theme.of(context)
                        .textTheme
                        .labelLarge
                        ?.copyWith(color: echoMuted),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.volume_down),
                  label: const Text('Play Original'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.mic),
                  label: const Text('Record'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DialogueLine extends StatelessWidget {
  final String speaker;
  final String text;
  const _DialogueLine({required this.speaker, required this.text});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          speaker,
          style: Theme.of(context)
              .textTheme
              .labelSmall
              ?.copyWith(color: echoMuted),
        ),
        const SizedBox(height: 6),
        Text(
          text,
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(color: echoDialogueGreen, fontStyle: FontStyle.italic),
        ),
      ],
    );
  }
}

