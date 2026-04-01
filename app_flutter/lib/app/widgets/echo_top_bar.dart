import 'package:flutter/material.dart';

import '../../core/theme/echo_theme.dart';

/// 对齐 Kotlin [com.example.englishchat.ui.components.EchoTopBar]
class EchoTopBar extends StatelessWidget {
  final String userDisplayName;
  final String userInitial;
  final VoidCallback onSignOut;
  /// 打开 Voice Lab（离线 STT / TTS 实验页）；为 null 时不显示入口。
  final VoidCallback? onOpenVoiceLab;

  const EchoTopBar({
    super.key,
    this.userDisplayName = 'GUEST',
    this.userInitial = 'G',
    this.onSignOut = _noop,
    this.onOpenVoiceLab,
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
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'MyEnglishChat',
                style: echoTypographyLogo,
              ),
              if (onOpenVoiceLab != null) ...[
                const SizedBox(width: 4),
                IconButton(
                  tooltip: 'Voice Lab',
                  onPressed: onOpenVoiceLab,
                  icon: const Icon(Icons.graphic_eq_outlined, size: 22),
                  color: echoMuted,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                ),
              ],
            ],
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
