import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';

class PracticeHomeScreen extends StatelessWidget {
  const PracticeHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'Practice（迁移中）\n请从 Shadowing 进入一个场景，再切到 Practice 子页。',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(color: echoMuted),
        ),
      ),
    );
  }
}

