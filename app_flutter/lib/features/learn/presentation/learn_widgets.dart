import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';

class LearnSearchField extends StatelessWidget {
  final String hintText;
  final ValueChanged<String> onChanged;

  const LearnSearchField({
    super.key,
    required this.hintText,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 44,
      decoration: BoxDecoration(
        color: echoSurface,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: echoBorder),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14),
      child: Row(
        children: [
          const Icon(Icons.search, size: 18, color: echoMuted),
          const SizedBox(width: 10),
          Expanded(
            child: TextField(
              onChanged: onChanged,
              decoration: InputDecoration(
                hintText: hintText,
                hintStyle: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: echoMuted),
                border: InputBorder.none,
                isCollapsed: true,
              ),
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: echoOnBackground),
            ),
          ),
        ],
      ),
    );
  }
}

class LearnBreadcrumb extends StatelessWidget {
  final List<String> items;

  const LearnBreadcrumb({super.key, required this.items});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 4,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        for (var i = 0; i < items.length; i++) ...[
          Text(
            items[i],
            style: Theme.of(context)
                .textTheme
                .labelSmall
                ?.copyWith(color: echoMuted),
          ),
          if (i != items.length - 1)
            const Text('›', style: TextStyle(color: echoMuted)),
        ],
      ],
    );
  }
}

class LearnLargeTitle extends StatelessWidget {
  final String title;
  const LearnLargeTitle({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, c) {
        final isNarrow = c.maxWidth < 420;
        final base = isNarrow
            ? Theme.of(context).textTheme.headlineLarge
            : Theme.of(context).textTheme.displaySmall;
        return Text(
          title,
          style: base?.copyWith(
            color: echoOnBackground,
            fontWeight: FontWeight.w600,
          ),
        );
      },
    );
  }
}

class LearnCard extends StatelessWidget {
  final Widget? leading;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final Widget? trailing;
  final int titleMaxLines;

  const LearnCard({
    super.key,
    this.leading,
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.trailing,
    this.titleMaxLines = 2,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: echoSurface,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: echoBorder),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              if (leading != null) ...[
                leading!,
                const SizedBox(width: 12),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      maxLines: titleMaxLines,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: echoOnBackground,
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            subtitle.toUpperCase(),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context)
                                .textTheme
                                .labelSmall
                                ?.copyWith(color: echoMuted),
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Icon(Icons.arrow_forward, size: 14, color: echoMuted),
                      ],
                    ),
                  ],
                ),
              ),
              if (trailing != null) ...[
                const SizedBox(width: 10),
                trailing!,
              ],
            ],
          ),
        ),
      ),
    );
  }
}

