import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/learn_demo_data.dart';
import '../domain/learn_models.dart';
import 'learn_session_screen.dart';
import 'learn_widgets.dart';

class LearnTopicScreen extends StatefulWidget {
  final LearnCategory category;
  final LearnScenario scenario;
  final LearnNpc npc;

  const LearnTopicScreen({
    super.key,
    required this.category,
    required this.scenario,
    required this.npc,
  });

  @override
  State<LearnTopicScreen> createState() => _LearnTopicScreenState();
}

class _LearnTopicScreenState extends State<LearnTopicScreen> {
  @override
  Widget build(BuildContext context) {
    final topics = demoTopics.where((t) => t.npcId == widget.npc.id);
    final filtered = topics.toList(growable: false);

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
                  '< BACK TO CHARACTERS',
                  style: Theme.of(context)
                      .textTheme
                      .labelMedium
                      ?.copyWith(color: echoMuted),
                ),
              ),
            ),
            LearnBreadcrumb(
              items: [
                'AI Scenarios',
                widget.category.title,
                widget.scenario.title,
                widget.npc.name,
              ],
            ),
            const SizedBox(height: 12),
            const LearnLargeTitle(title: 'Select a Topic'),
            const SizedBox(height: 18),
            Expanded(
              child: ListView.separated(
                itemCount: filtered.length,
                separatorBuilder: (_, __) => const SizedBox(height: 14),
                itemBuilder: (context, i) {
                  final t = filtered[i];
                  return LearnCard(
                    title: t.title,
                    subtitle: t.subtitle,
                    onTap: () {
                      Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => LearnSessionScreen(
                            category: widget.category,
                            scenario: widget.scenario,
                            npc: widget.npc,
                            topic: t,
                          ),
                        ),
                      );
                    },
                    titleMaxLines: 2,
                    trailing: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: echoNavSelectedCircle,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(color: echoBorder),
                      ),
                      alignment: Alignment.center,
                      child: const Icon(Icons.play_arrow, size: 18),
                    ),
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

