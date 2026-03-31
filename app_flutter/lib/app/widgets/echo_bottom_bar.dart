import 'package:flutter/material.dart';

import '../../core/theme/echo_theme.dart';

/// 对齐 Kotlin [com.example.englishchat.ui.components.EchoBottomBar]
///
/// [routes] 与 [onNavigate] 使用与产品 IA 一致的 route 名：`learn` / `p2p_match` / `profile`
class EchoBottomBar extends StatelessWidget {
  final String currentRoute;
  final ValueChanged<String> onNavigate;

  const EchoBottomBar({
    super.key,
    required this.currentRoute,
    required this.onNavigate,
  });

  static const _items = [
    _EchoNavItem(route: 'learn', label: 'LEARN', icon: Icons.school),
    _EchoNavItem(route: 'p2p_match', label: 'P2P MATCH', icon: Icons.people),
    _EchoNavItem(route: 'profile', label: 'PROFILE', icon: Icons.settings),
  ];

  @override
  Widget build(BuildContext context) {
    final outline = Theme.of(context).colorScheme.outline;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Divider(
          height: 1,
          thickness: 1,
          color: outline.withValues(alpha: 0.5),
        ),
        Material(
          color: Theme.of(context).colorScheme.surface,
          child: Padding(
            padding: const EdgeInsets.only(top: 10, bottom: 12),
            child: Row(
              children: [
                for (final item in _items)
                  Expanded(
                    child: _EchoNavCell(
                      item: item,
                      selected: currentRoute == item.route,
                      onTap: () => onNavigate(item.route),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _EchoNavItem {
  final String route;
  final String label;
  final IconData icon;

  const _EchoNavItem({
    required this.route,
    required this.label,
    required this.icon,
  });
}

class _EchoNavCell extends StatelessWidget {
  final _EchoNavItem item;
  final bool selected;
  final VoidCallback onTap;

  const _EchoNavCell({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final fg = selected ? echoOnBackground : echoMuted;

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 48,
              height: 48,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: selected ? echoNavSelectedCircle : Theme.of(context).colorScheme.surface,
                shape: BoxShape.circle,
              ),
              child: Icon(item.icon, size: 22, color: fg),
            ),
            const SizedBox(height: 6),
            Text(
              item.label,
              textAlign: TextAlign.center,
              maxLines: 2,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    fontWeight: selected ? FontWeight.bold : FontWeight.w500,
                    color: fg,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
