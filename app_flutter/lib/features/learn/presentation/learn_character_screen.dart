import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/learn_demo_data.dart';
import '../domain/learn_models.dart';
import 'learn_topic_screen.dart';
import 'learn_widgets.dart';

class LearnCharacterScreen extends StatefulWidget {
  final LearnCategory category;
  final LearnScenario scenario;

  const LearnCharacterScreen({
    super.key,
    required this.category,
    required this.scenario,
  });

  @override
  State<LearnCharacterScreen> createState() => _LearnCharacterScreenState();
}

class _LearnCharacterScreenState extends State<LearnCharacterScreen> {
  @override
  Widget build(BuildContext context) {
    final npcs = demoNpcs.where((n) => n.scenarioId == widget.scenario.id);
    final filtered = npcs.toList(growable: false);

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20).copyWith(bottom: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 10),
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
            LearnBreadcrumb(
              items: ['AI Scenarios', widget.category.title, widget.scenario.title],
            ),
            const SizedBox(height: 12),
            const LearnLargeTitle(title: 'Select a Character'),
            const SizedBox(height: 18),
            Expanded(
              child: LayoutBuilder(
                builder: (context, c) {
                  final isWide = c.maxWidth >= 860;
                  final cross = isWide ? 3 : (c.maxWidth >= 600 ? 2 : 1);
                  return GridView.count(
                    crossAxisCount: cross,
                    crossAxisSpacing: 14,
                    mainAxisSpacing: 14,
                    childAspectRatio: isWide ? 1.25 : 1.2,
                    children: [
                      for (final npc in filtered)
                        LearnCard(
                          leading: _Avatar(initials: npc.initials),
                          title: npc.name,
                          subtitle: 'View topics',
                          onTap: () {
                            Navigator.of(context).push(
                              MaterialPageRoute<void>(
                                builder: (_) => LearnTopicScreen(
                                  category: widget.category,
                                  scenario: widget.scenario,
                                  npc: npc,
                                ),
                              ),
                            );
                          },
                          trailing: const Icon(Icons.chevron_right, color: echoMuted),
                        ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  final String initials;
  const _Avatar({required this.initials});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 48,
      height: 48,
      decoration: const BoxDecoration(
        color: echoOnBackground,
        shape: BoxShape.circle,
      ),
      alignment: Alignment.center,
      child: Text(
        initials.toUpperCase(),
        style: Theme.of(context)
            .textTheme
            .titleMedium
            ?.copyWith(color: Colors.white, fontWeight: FontWeight.bold),
      ),
    );
  }
}

