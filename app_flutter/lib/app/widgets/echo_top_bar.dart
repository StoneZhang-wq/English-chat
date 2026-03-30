import 'package:flutter/material.dart';

import '../../core/theme/echo_theme.dart';

/// 对齐 Kotlin [com.example.englishchat.ui.components.EchoTopBar]
class EchoTopBar extends StatelessWidget {
  final String userDisplayName;
  final String userInitial;
  final VoidCallback onSignOut;

  const EchoTopBar({
    super.key,
    this.userDisplayName = 'GUEST',
    this.userInitial = 'G',
    this.onSignOut = _noop,
  });

  static void _noop() {}

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            'MyEnglishChat',
            style: echoTypographyLogo,
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    userDisplayName.toUpperCase(),
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: echoOnBackground,
                        ),
                  ),
                  InkWell(
                    onTap: onSignOut,
                    child: Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        'SIGN OUT',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: echoMuted,
                            ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 12),
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                  color: echoOnBackground,
                  shape: BoxShape.circle,
                ),
                child: Text(
                  userInitial.toUpperCase(),
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                      ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
