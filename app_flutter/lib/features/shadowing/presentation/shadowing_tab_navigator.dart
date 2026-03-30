import 'package:flutter/material.dart';

import '../../session/presentation/scenario_session_screen.dart';
import '../domain/shadowing_routes.dart';
import 'shadowing_home_screen.dart';

/// Shadowing Tab 内嵌导航：列表与 [ScenarioSessionScreen] 同处外壳顶栏/底栏之下（对齐 Kotlin MainScreen + NavHost）
class ShadowingTabNavigator extends StatelessWidget {
  final GlobalKey<NavigatorState> navigatorKey;

  const ShadowingTabNavigator({
    super.key,
    required this.navigatorKey,
  });

  @override
  Widget build(BuildContext context) {
    return Navigator(
      key: navigatorKey,
      initialRoute: ShadowingRoutes.home,
      onGenerateRoute: (settings) {
        switch (settings.name) {
          case ShadowingRoutes.home:
            return MaterialPageRoute<void>(
              builder: (_) => const ShadowingHomeScreen(),
              settings: settings,
            );
          case ShadowingRoutes.session:
            final title = settings.arguments as String? ?? '';
            return MaterialPageRoute<void>(
              builder: (_) => ScenarioSessionScreen(scenarioTitle: title),
              settings: settings,
            );
          default:
            return MaterialPageRoute<void>(
              builder: (_) => const ShadowingHomeScreen(),
              settings: const RouteSettings(name: ShadowingRoutes.home),
            );
        }
      },
    );
  }
}
