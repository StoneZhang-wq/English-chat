import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/shadowing_routes.dart';

/// 设计稿背景（略亮于 Echo 全局底，突出「选题」区域）
const _pickPageBg = Color(0xFFF8F8F8);

class _ScenarioPickItem {
  final String title;
  final String exampleLine;

  const _ScenarioPickItem({
    required this.title,
    required this.exampleLine,
  });
}

class ShadowingHomeScreen extends StatefulWidget {
  const ShadowingHomeScreen({super.key});

  @override
  State<ShadowingHomeScreen> createState() => _ShadowingHomeScreenState();
}

class _ShadowingHomeScreenState extends State<ShadowingHomeScreen> {
  final _searchController = TextEditingController();

  static const _scenarios = [
    _ScenarioPickItem(
      title: 'Hotel Check-in',
      exampleLine:
          'Hello, I have a reservation under the name Smith for three nights.',
    ),
    _ScenarioPickItem(
      title: 'Job Interview',
      exampleLine:
          'I\'m excited to walk you through my background and how I can contribute to your team.',
    ),
    _ScenarioPickItem(
      title: 'Doctor Appointment',
      exampleLine:
          'I\'ve had this cough for about a week now, and it doesn\'t seem to be getting better.',
    ),
    _ScenarioPickItem(
      title: 'Coffee Shop',
      exampleLine:
          'Could I get a medium latte with oat milk, please? And a croissant if you have one.',
    ),
  ];

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  TextStyle get _titleItalicSerif => GoogleFonts.playfairDisplay(
        fontSize: 32,
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.italic,
        height: 1.15,
        color: echoOnBackground,
      );

  TextStyle get _subtitleCaps => GoogleFonts.inter(
        fontSize: 11,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.9,
        color: echoMuted,
      );

  TextStyle _cardTitle(BuildContext context) => GoogleFonts.playfairDisplay(
        fontSize: 18,
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.italic,
        height: 1.25,
        color: echoOnBackground,
      );

  TextStyle _cardExample() => GoogleFonts.inter(
        fontSize: 13,
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.italic,
        height: 1.45,
        color: echoMuted,
      );

  void _onRequestScenario() {
    final q = _searchController.text.trim();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          q.isEmpty
              ? '请输入想练习的场景，后续将接入智能推荐'
              : '将为你匹配「$q」类场景（占位）',
        ),
      ),
    );
  }

  void _openScenario(String title) {
    Navigator.of(context).pushNamed(
      ShadowingRoutes.session,
      arguments: title,
    );
  }

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: _pickPageBg,
      child: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(22, 20, 22, 28),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                Text('Pick a Scenario', style: _titleItalicSerif),
                const SizedBox(height: 10),
                Text(
                  'RECOMMENDED FOR YOU TODAY',
                  style: _subtitleCaps,
                ),
                const SizedBox(height: 22),
                _SearchRequestBar(
                  controller: _searchController,
                  onRequest: _onRequestScenario,
                ),
                const SizedBox(height: 24),
              ]),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 22),
            sliver: SliverGrid(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                mainAxisSpacing: 14,
                crossAxisSpacing: 14,
                childAspectRatio: 0.72,
              ),
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final item = _scenarios[index];
                  return _ScenarioPickCard(
                    item: item,
                    titleStyle: _cardTitle(context),
                    exampleStyle: _cardExample(),
                    onTap: () => _openScenario(item.title),
                  );
                },
                childCount: _scenarios.length,
              ),
            ),
          ),
          const SliverPadding(padding: EdgeInsets.only(bottom: 24)),
        ],
      ),
    );
  }
}

class _SearchRequestBar extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onRequest;

  const _SearchRequestBar({
    required this.controller,
    required this.onRequest,
  });

  @override
  Widget build(BuildContext context) {
    final hintStyle = GoogleFonts.inter(
      fontSize: 14,
      color: echoMuted.withValues(alpha: 0.85),
    );

    return Container(
      decoration: BoxDecoration(
        color: echoSurface,
        borderRadius: BorderRadius.circular(999),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
        border: Border.all(color: echoBorder.withValues(alpha: 0.6)),
      ),
      padding: const EdgeInsets.only(left: 18, right: 6, top: 4, bottom: 4),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              style: GoogleFonts.inter(fontSize: 14, color: echoOnBackground),
              decoration: InputDecoration(
                isDense: true,
                border: InputBorder.none,
                hintText:
                    'What do you want to practice? (e.g., \'at the dentist\')',
                hintStyle: hintStyle,
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
              ),
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => onRequest(),
            ),
          ),
          const SizedBox(width: 6),
          Material(
            color: echoOnBackground,
            borderRadius: BorderRadius.circular(999),
            child: InkWell(
              onTap: onRequest,
              borderRadius: BorderRadius.circular(999),
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.auto_awesome, color: Colors.white, size: 16),
                    const SizedBox(width: 6),
                    Text(
                      'REQUEST',
                      style: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.6,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ScenarioPickCard extends StatelessWidget {
  final _ScenarioPickItem item;
  final TextStyle titleStyle;
  final TextStyle exampleStyle;
  final VoidCallback onTap;

  const _ScenarioPickCard({
    required this.item,
    required this.titleStyle,
    required this.exampleStyle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(28),
        child: Ink(
          decoration: BoxDecoration(
            color: echoSurface,
            borderRadius: BorderRadius.circular(28),
            border: Border.all(color: echoBorder),
          ),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.title, style: titleStyle),
                const SizedBox(height: 12),
                Expanded(
                  child: Text(
                    item.exampleLine,
                    style: exampleStyle,
                    maxLines: 5,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
