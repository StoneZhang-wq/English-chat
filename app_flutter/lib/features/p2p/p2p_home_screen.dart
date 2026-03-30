import 'package:flutter/material.dart';

import '../../core/theme/echo_theme.dart';

class P2pHomeScreen extends StatelessWidget {
  const P2pHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'P2P Roleplay（开发中）\n后续接入 Agora/TRTC，并由 backend 下发 Token。',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(color: echoMuted),
        ),
      ),
    );
  }
}

