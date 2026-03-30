import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../../practice/presentation/practice_session_panel.dart';
import '../../shadowing/presentation/shadowing_session_panel.dart';

/// 场景练习页。顶栏由 [HomeScreen] 外壳统一提供，此处不再叠一层 [EchoTopBar]（对齐 Kotlin 在 NavHost 内的可视区域）
class ScenarioSessionScreen extends StatefulWidget {
  final String scenarioTitle;
  final int moduleNumber;
  const ScenarioSessionScreen({
    super.key,
    required this.scenarioTitle,
    this.moduleNumber = 1,
  });

  @override
  State<ScenarioSessionScreen> createState() => _ScenarioSessionScreenState();
}

class _ScenarioSessionScreenState extends State<ScenarioSessionScreen> {
  int _innerTab = 0; // 0 shadowing, 1 practice

  @override
  Widget build(BuildContext context) {
    final modeLabel = _innerTab == 0 ? 'SHADOWING' : 'PRACTICE';

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20).copyWith(bottom: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            InkWell(
              onTap: () => Navigator.of(context).maybePop(),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(
                  '< BACK TO SCENARIOS',
                  style: Theme.of(context)
                      .textTheme
                      .labelMedium
                      ?.copyWith(color: echoMuted),
                ),
              ),
            ),
            const SizedBox(height: 4),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    widget.scenarioTitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context)
                        .textTheme
                        .headlineMedium
                        ?.copyWith(color: echoOnBackground),
                  ),
                ),
                if (_innerTab == 1)
                  IconButton(
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('生成复习资料：后续版本开放')),
                      );
                    },
                    icon: const Icon(Icons.description, color: echoSubtitleCaps),
                    tooltip: '生成复习资料',
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'MODULE ${widget.moduleNumber.toString().padLeft(2, '0')} / $modeLabel',
              style: Theme.of(context)
                  .textTheme
                  .labelSmall
                  ?.copyWith(color: echoMuted),
            ),
            const SizedBox(height: 16),
            _InnerModeTabs(
              selectedIndex: _innerTab,
              onSelect: (i) => setState(() => _innerTab = i),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: _innerTab == 0
                  ? const ShadowingSessionPanel()
                  : PracticeSessionPanel(scenarioTitle: widget.scenarioTitle),
            ),
          ],
        ),
      ),
    );
  }
}

class _InnerModeTabs extends StatelessWidget {
  final int selectedIndex;
  final ValueChanged<int> onSelect;
  const _InnerModeTabs({
    required this.selectedIndex,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: echoSurface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: echoBorder),
      ),
      child: Row(
        children: [
          Expanded(
            child: _InnerTabItem(
              label: '1. SHADOWING',
              icon: Icons.headphones,
              selected: selectedIndex == 0,
              onTap: () => onSelect(0),
            ),
          ),
          Expanded(
            child: _InnerTabItem(
              label: '2. PRACTICE',
              icon: Icons.chat_bubble_outline,
              selected: selectedIndex == 1,
              onTap: () => onSelect(1),
            ),
          ),
        ],
      ),
    );
  }
}

class _InnerTabItem extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  const _InnerTabItem({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final fg = selected ? echoOnBackground : echoMuted;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 18, color: fg),
                const SizedBox(width: 6),
                Flexible(
                  child: Text(
                    label,
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: fg,
                          fontWeight: selected ? FontWeight.bold : FontWeight.w500,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Container(
              height: 2,
              width: double.infinity,
              color: selected ? echoOnBackground : Colors.transparent,
            ),
          ],
        ),
      ),
    );
  }
}
