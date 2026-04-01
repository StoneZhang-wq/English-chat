import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../../p2p_match/domain/p2p_models.dart';
import '../../p2p_match/presentation/p2p_matching_screen.dart';
import '../../practice/presentation/practice_session_panel.dart';
import '../../shadowing/presentation/shadowing_session_panel.dart';
import '../domain/learn_models.dart';
import 'learn_widgets.dart';

class LearnSessionScreen extends StatefulWidget {
  final LearnCategory category;
  final LearnScenario scenario;
  final LearnNpc npc;
  final LearnTopic topic;

  const LearnSessionScreen({
    super.key,
    required this.category,
    required this.scenario,
    required this.npc,
    required this.topic,
  });

  @override
  State<LearnSessionScreen> createState() => _LearnSessionScreenState();
}

class _LearnSessionScreenState extends State<LearnSessionScreen> {
  int _mode = 0; // 0 shadowing, 1 practice, 2 ai dialogue

  P2pScenarioCard _p2pScenarioFromTopic() {
    return P2pScenarioCard(
      id: 'learn_${widget.topic.id}',
      title: widget.topic.title,
      categoryLabel: widget.category.title,
      scenarioLabel: widget.scenario.title,
      task: widget.topic.subtitle,
    );
  }

  @override
  Widget build(BuildContext context) {
    final modeLabel = switch (_mode) {
      0 => 'SHADOWING',
      1 => 'PRACTICE',
      _ => 'AI DIALOGUE',
    };

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
                  '< BACK TO TOPICS',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: echoMuted,
                      ),
                ),
              ),
            ),
            const SizedBox(height: 2),
            LearnBreadcrumb(
              items: [
                'AI Scenarios',
                widget.category.title,
                widget.scenario.title,
                widget.npc.name,
              ],
            ),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    widget.topic.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          color: echoOnBackground,
                        ),
                  ),
                ),
                if (_mode == 2)
                  Padding(
                    padding: const EdgeInsets.only(right: 4),
                    child: FilledButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => P2pMatchingScreen(
                              selected: _p2pScenarioFromTopic(),
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.people, size: 18),
                      label: Text(
                        '真人实战',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                      ),
                      style: FilledButton.styleFrom(
                        backgroundColor: echoOnBackground,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 10,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                if (_mode != 0)
                  IconButton(
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Review：后续版本开放')),
                      );
                    },
                    icon: const Icon(Icons.description, color: echoSubtitleCaps),
                    tooltip: 'Review',
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'MODULE 01 / $modeLabel',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: echoMuted,
                  ),
            ),
            const SizedBox(height: 16),
            _LearnModeTabs(
              selectedIndex: _mode,
              onSelect: (i) => setState(() => _mode = i),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: IndexedStack(
                index: _mode,
                children: [
                  const ShadowingSessionPanel(),
                  PracticeSessionPanel(
                    key: const ValueKey('practice_session_panel'),
                    scenarioTitle: widget.topic.title,
                  ),
                  PracticeSessionPanel(
                    key: const ValueKey('ai_dialogue_session_panel'),
                    scenarioTitle: widget.topic.title,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LearnModeTabs extends StatelessWidget {
  final int selectedIndex;
  final ValueChanged<int> onSelect;

  const _LearnModeTabs({
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
            child: _TabItem(
              label: '1. SHADOWING',
              selected: selectedIndex == 0,
              onTap: () => onSelect(0),
            ),
          ),
          Expanded(
            child: _TabItem(
              label: '2. PRACTICE',
              selected: selectedIndex == 1,
              onTap: () => onSelect(1),
            ),
          ),
          Expanded(
            child: _TabItem(
              label: '3. AI DIALOGUE',
              selected: selectedIndex == 2,
              onTap: () => onSelect(2),
            ),
          ),
        ],
      ),
    );
  }
}

class _TabItem extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _TabItem({
    required this.label,
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
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 2,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: fg,
                    fontWeight: selected ? FontWeight.bold : FontWeight.w500,
                  ),
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

