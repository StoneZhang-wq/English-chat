import 'package:flutter/material.dart';

import 'learn_category_screen.dart';

class LearnNavigator extends StatelessWidget {
  final GlobalKey<NavigatorState> navigatorKey;

  const LearnNavigator({super.key, required this.navigatorKey});

  @override
  Widget build(BuildContext context) {
    return Navigator(
      key: navigatorKey,
      onGenerateRoute: (settings) {
        return MaterialPageRoute<void>(
          settings: settings,
          builder: (_) => const LearnCategoryScreen(),
        );
      },
    );
  }
}

