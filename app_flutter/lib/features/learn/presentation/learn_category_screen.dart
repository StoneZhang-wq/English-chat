import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/learn_demo_data.dart';
import '../domain/learn_models.dart';
import 'learn_session_screen.dart';
import 'learn_scenario_screen.dart';
import 'learn_widgets.dart';

class LearnCategoryScreen extends StatefulWidget {
  const LearnCategoryScreen({super.key});

  @override
  State<LearnCategoryScreen> createState() => _LearnCategoryScreenState();
}

class _LearnCategoryScreenState extends State<LearnCategoryScreen> {
  String _q = '';

  List<_TopicHit> get _topicHits {
    final query = _q.trim().toLowerCase();
    if (query.isEmpty) return const [];

    final catById = {for (final c in demoCategories) c.id: c};
    final scenarioById = {for (final s in demoScenarios) s.id: s};
    final npcById = {for (final n in demoNpcs) n.id: n};

    bool matchAny(Iterable<String> fields) {
      for (final f in fields) {
        if (f.toLowerCase().contains(query)) return true;
      }
      return false;
    }

    final hits = <_TopicHit>[];
    for (final t in demoTopics) {
      final npc = npcById[t.npcId];
      final scenario = npc == null ? null : scenarioById[npc.scenarioId];
      final cat = scenario == null ? null : catById[scenario.categoryId];

      final fields = <String>[
        t.title,
        t.subtitle,
        if (npc != null) npc.name,
        if (npc != null) npc.description,
        if (scenario != null) scenario.title,
        if (cat != null) cat.title,
      ];

      if (matchAny(fields)) {
        hits.add(_TopicHit(
          category: cat,
          scenario: scenario,
          npc: npc,
          topic: t,
        ));
      }
    }

    return hits;
  }

  @override
  Widget build(BuildContext context) {
    final showSearchResults = _q.trim().isNotEmpty;
    final hits = _topicHits;
    final filteredCategories = demoCategories.toList(growable: false);

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20).copyWith(bottom: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 10),
            const Text('AI Scenarios', style: TextStyle(color: echoMuted)),
            const SizedBox(height: 10),
            const LearnLargeTitle(title: 'Select a Category'),
            const SizedBox(height: 14),
            LearnSearchField(
              hintText: 'Search topics, characters...',
              onChanged: (v) => setState(() => _q = v),
            ),
            const SizedBox(height: 18),
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 360),
                reverseDuration: const Duration(milliseconds: 260),
                switchInCurve: Curves.easeOutCubic,
                switchOutCurve: Curves.easeInCubic,
                transitionBuilder: (child, animation) {
                  final isExit = animation.status == AnimationStatus.reverse;
                  final offset = isExit
                      ? Tween<Offset>(
                          begin: Offset.zero,
                          end: const Offset(0, -0.08),
                        ).animate(animation)
                      : Tween<Offset>(
                          begin: const Offset(0, 0.08),
                          end: Offset.zero,
                        ).animate(animation);
                  return FadeTransition(
                    opacity: animation,
                    child: SlideTransition(position: offset, child: child),
                  );
                },
                child: showSearchResults
                    ? _SearchResultsList(
                        key: const ValueKey('search_results'),
                        query: _q.trim(),
                        hits: hits,
                      )
                    : _CategoryGrid(
                        key: const ValueKey('categories'),
                        categories: filteredCategories,
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CategoryGrid extends StatelessWidget {
  final List<LearnCategory> categories;
  const _CategoryGrid({super.key, required this.categories});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, c) {
        final isWide = c.maxWidth >= 860;
        final cross = isWide ? 3 : (c.maxWidth >= 600 ? 2 : 1);
        return GridView.count(
          crossAxisCount: cross,
          crossAxisSpacing: 14,
          mainAxisSpacing: 14,
          childAspectRatio: isWide ? 2.65 : 2.4,
          children: [
            for (final cat in categories) _CategoryCard(cat: cat),
          ],
        );
      },
    );
  }
}

class _SearchResultsList extends StatelessWidget {
  final String query;
  final List<_TopicHit> hits;

  const _SearchResultsList({
    super.key,
    required this.query,
    required this.hits,
  });

  @override
  Widget build(BuildContext context) {
    if (hits.isEmpty) {
      return Center(
        child: Text(
          'No results for “$query”',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: echoMuted),
        ),
      );
    }

    return ListView.separated(
      itemCount: hits.length,
      separatorBuilder: (_, __) => const SizedBox(height: 14),
      itemBuilder: (context, i) {
        final h = hits[i];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (h.category != null || h.scenario != null || h.npc != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 6, left: 6),
                child: LearnBreadcrumb(
                  items: [
                    if (h.category != null) h.category!.title,
                    if (h.scenario != null) h.scenario!.title,
                    if (h.npc != null) h.npc!.name,
                  ],
                ),
              ),
            LearnCard(
              title: h.topic.title,
              subtitle: h.topic.subtitle,
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
              onTap: () {
            final cat = h.category ?? demoCategories.first;
            final sc = h.scenario ?? demoScenarios.first;
            final npc = h.npc ?? demoNpcs.first;
            Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => LearnSessionScreen(
                  category: cat,
                  scenario: sc,
                  npc: npc,
                  topic: h.topic,
                ),
              ),
            );
              },
            ),
          ],
        );
      },
    );
  }
}

class _TopicHit {
  final LearnCategory? category;
  final LearnScenario? scenario;
  final LearnNpc? npc;
  final LearnTopic topic;

  const _TopicHit({
    required this.category,
    required this.scenario,
    required this.npc,
    required this.topic,
  });
}

class _CategoryCard extends StatelessWidget {
  final LearnCategory cat;
  const _CategoryCard({required this.cat});

  @override
  Widget build(BuildContext context) {
    return LearnCard(
      title: cat.title,
      subtitle: cat.subtitle,
      onTap: () {
        Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) => LearnScenarioScreen(category: cat),
          ),
        );
      },
    );
  }
}

