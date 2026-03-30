import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';

/// 对齐 Kotlin [AiDialogueScreen]（仅内容区；顶栏由 [HomeScreen] 统一提供）
class AiDialogueHomeScreen extends StatelessWidget {
  const AiDialogueHomeScreen({super.key});

  static const _categories = [
    _AiCategory(
      title: 'Travel & Exploration',
      description: 'Master the language of the world',
    ),
    _AiCategory(
      title: 'Professional Life',
      description: 'Excel in your career conversations',
    ),
    _AiCategory(
      title: 'Daily Life & Culture',
      description: 'Navigate real situations with confidence',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
      children: [
        Text(
          'AI Dialogue',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                color: echoOnBackground,
              ),
        ),
        const SizedBox(height: 8),
        Text(
          'SELECT A CATEGORY TO BEGIN YOUR JOURNEY',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: echoMuted,
              ),
        ),
        const SizedBox(height: 16),
        for (final c in _categories) ...[
          _AiCategoryCard(category: c),
          const SizedBox(height: 16),
        ],
      ],
    );
  }
}

class _AiCategory {
  final String title;
  final String description;
  const _AiCategory({required this.title, required this.description});
}

class _AiCategoryCard extends StatelessWidget {
  final _AiCategory category;
  const _AiCategoryCard({required this.category});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 168,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('「${category.title}」待接入对话流')),
            );
          },
          borderRadius: BorderRadius.circular(20),
          child: Ink(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: echoBorder),
            ),
            child: Stack(
              fit: StackFit.expand,
              children: [
                DecoratedBox(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(19),
                    color: const Color(0xFFE0E0E0),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: FractionallySizedBox(
                      widthFactor: 0.62,
                      alignment: Alignment.centerLeft,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            category.title,
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  color: echoOnBackground,
                                ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            category.description,
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: echoMuted,
                                ),
                          ),
                        ],
                      ),
                    ),
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
