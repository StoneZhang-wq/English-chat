import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/learn_demo_data.dart';
import '../domain/learn_models.dart';
import 'learn_character_screen.dart';
import 'learn_widgets.dart';

class LearnScenarioScreen extends StatefulWidget {
  final LearnCategory category;
  const LearnScenarioScreen({super.key, required this.category});

  @override
  State<LearnScenarioScreen> createState() => _LearnScenarioScreenState();
}

class _LearnScenarioScreenState extends State<LearnScenarioScreen> {
  @override
  Widget build(BuildContext context) {
    final scenarios = demoScenarios.where((s) => s.categoryId == widget.category.id);
    final filtered = scenarios.toList(growable: false);

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
                  '< BACK TO CATEGORIES',
                  style: Theme.of(context)
                      .textTheme
                      .labelMedium
                      ?.copyWith(color: echoMuted),
                ),
              ),
            ),
            LearnBreadcrumb(items: ['AI Scenarios', widget.category.title]),
            const SizedBox(height: 12),
            const LearnLargeTitle(title: 'Select a Scenario'),
            const SizedBox(height: 18),
            Expanded(
              child: ListView.separated(
                itemCount: filtered.length,
                separatorBuilder: (_, __) => const SizedBox(height: 14),
                itemBuilder: (context, i) {
                  final s = filtered[i];
                  return LearnCard(
                    leading: Container(
                      width: 64,
                      height: 44,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: echoBorder),
                        gradient: const LinearGradient(
                          colors: [Color(0xFF2C2C2C), Color(0xFF111111)],
                        ),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        s.title.substring(0, 1),
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ),
                    title: s.title,
                    subtitle: s.subtitle,
                    titleMaxLines: 2,
                    onTap: () {
                      Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => LearnCharacterScreen(
                            category: widget.category,
                            scenario: s,
                          ),
                        ),
                      );
                    },
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

