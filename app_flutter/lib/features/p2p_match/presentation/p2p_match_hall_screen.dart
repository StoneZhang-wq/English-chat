import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/p2p_demo_data.dart';
import '../domain/p2p_models.dart';
import 'p2p_matching_screen.dart';

class P2pMatchHallScreen extends StatelessWidget {
  const P2pMatchHallScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20).copyWith(bottom: 8),
        child: Column(
          children: [
            const SizedBox(height: 14),
            const _P2pHallHero(),
            const SizedBox(height: 26),
            Expanded(
              child: LayoutBuilder(
                builder: (context, c) {
                  final isWide = c.maxWidth >= 860;
                  return isWide
                      ? Row(
                          children: const [
                            Expanded(child: _RecentPracticeCard()),
                            SizedBox(width: 16),
                            Expanded(child: _TrendingNowList()),
                          ],
                        )
                      : const Column(
                          children: [
                            _RecentPracticeCard(compact: true),
                            SizedBox(height: 14),
                            Expanded(child: _TrendingNowList()),
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

class _P2pHallHero extends StatelessWidget {
  const _P2pHallHero();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 54,
          height: 54,
          decoration: BoxDecoration(
            color: echoOnBackground,
            borderRadius: BorderRadius.circular(18),
          ),
          alignment: Alignment.center,
          child: const Icon(Icons.people, color: Colors.white, size: 26),
        ),
        const SizedBox(height: 14),
        Text(
          'P2P Match Hall',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontStyle: FontStyle.italic,
                fontFamily: 'serif',
              ),
        ),
        const SizedBox(height: 6),
        Text(
          'REAL CONVERSATIONS WITH REAL PEOPLE',
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: echoMuted,
                letterSpacing: 1.2,
              ),
        ),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String label;
  const _SectionHeader({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 14, color: echoMuted),
        const SizedBox(width: 8),
        Text(
          label.toUpperCase(),
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: echoMuted,
                letterSpacing: 1.1,
              ),
        ),
      ],
    );
  }
}

class _RecentPracticeCard extends StatelessWidget {
  final bool compact;
  const _RecentPracticeCard({this.compact = false});

  @override
  Widget build(BuildContext context) {
    final card = Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: echoSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: echoBorder),
      ),
      child: Center(
        child: Text(
          'No recent practice found. Start a scenario in the Learning module!',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: echoMuted),
        ),
      ),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: Icons.history, label: 'Recent practice'),
        const SizedBox(height: 10),
        if (compact)
          SizedBox(height: 92, child: card)
        else
          Expanded(child: card),
      ],
    );
  }
}

class _TrendingNowList extends StatelessWidget {
  const _TrendingNowList();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: Icons.local_fire_department, label: 'Trending now'),
        const SizedBox(height: 10),
        Expanded(
          child: ListView.separated(
            itemCount: demoTrending.length,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final card = demoTrending[i];
              return _TrendingTile(card: card);
            },
          ),
        ),
      ],
    );
  }
}

class _TrendingTile extends StatelessWidget {
  final P2pScenarioCard card;
  const _TrendingTile({required this.card});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: echoSurface,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => P2pMatchingScreen(selected: card),
            ),
          );
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: echoBorder),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      card.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontFamily: 'serif',
                            fontStyle: FontStyle.italic,
                            fontWeight: FontWeight.w400,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${card.categoryLabel.toUpperCase()} • ${card.scenarioLabel.toUpperCase()}',
                      style: Theme.of(context)
                          .textTheme
                          .labelSmall
                          ?.copyWith(color: echoMuted),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: echoNavSelectedCircle,
                  borderRadius: BorderRadius.circular(17),
                  border: Border.all(color: echoBorder),
                ),
                alignment: Alignment.center,
                child: const Icon(Icons.play_arrow, size: 18),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

