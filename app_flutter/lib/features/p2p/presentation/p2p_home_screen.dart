import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';

class P2pHomeScreen extends StatelessWidget {
  const P2pHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
      child: Column(
        children: [
          const SizedBox(height: 16),
          Container(
            width: 88,
            height: 88,
            decoration: BoxDecoration(
              color: echoOnBackground,
              borderRadius: BorderRadius.circular(22),
            ),
            alignment: Alignment.center,
            child: const Icon(Icons.people, color: Colors.white, size: 40),
          ),
          const SizedBox(height: 20),
          Text(
            'P2P Roleplay',
            textAlign: TextAlign.center,
            style: echoTypographyP2pTitle,
          ),
          const SizedBox(height: 10),
          Text(
            'Practice with real people in guided scenarios.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: echoMuted),
          ),
          const SizedBox(height: 28),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _P2pFeatureCard(
                  title: 'SAFE SPACE',
                  body: 'Strict community guidelines.',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _P2pFeatureCard(
                  title: 'EARN POINTS',
                  body: 'Level up your fluency.',
                ),
              ),
            ],
          ),
          const SizedBox(height: 28),
          SizedBox(
            width: double.infinity,
            height: 52,
            child: FilledButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('匹配功能：待接入 Agora/TRTC + backend Token')),
                );
              },
              style: FilledButton.styleFrom(
                backgroundColor: echoOnBackground,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: Text(
                'FIND A PARTNER',
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _P2pFeatureCard extends StatelessWidget {
  final String title;
  final String body;

  const _P2pFeatureCard({
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: echoSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: echoBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: echoOnBackground,
                ),
          ),
          const SizedBox(height: 6),
          Text(
            body,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: echoMuted),
          ),
        ],
      ),
    );
  }
}
