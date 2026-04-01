import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';

class ProfileHomeScreen extends StatelessWidget {
  const ProfileHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20).copyWith(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 10),
          Text(
            'Profile',
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
                  color: echoOnBackground,
                  fontWeight: FontWeight.w600,
                ),
          ),
          const SizedBox(height: 14),
          Text(
            '个人中心 / 设置（后续版本落地：学习数据、偏好、账号等）。',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: echoMuted,
                ),
          ),
        ],
      ),
    );
  }
}

