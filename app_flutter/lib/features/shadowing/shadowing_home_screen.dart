import 'package:flutter/material.dart';

import '../../core/theme/echo_theme.dart';
import '../session/scenario_session_screen.dart';

class ShadowingHomeScreen extends StatelessWidget {
  const ShadowingHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Kotlin 端 ShadowingScreen 目前是场景列表占位，这里先提供一个示例入口
    final scenarios = const [
      'Hotel Check-in',
      'Job Interview',
      'Doctor Appointment',
    ];

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'SHADOWING',
            style: Theme.of(context)
                .textTheme
                .labelLarge
                ?.copyWith(color: echoMuted),
          ),
          const SizedBox(height: 8),
          Text(
            'Choose a scenario',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Expanded(
            child: ListView.separated(
              itemCount: scenarios.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final title = scenarios[i];
                return InkWell(
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => ScenarioSessionScreen(scenarioTitle: title),
                      ),
                    );
                  },
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: echoSurface,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: echoBorder),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.headphones, color: echoDialogueGreen),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            title,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                        const Icon(Icons.chevron_right, color: echoMuted),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

