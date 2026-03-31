import 'package:flutter/material.dart';

import 'p2p_home_screen.dart';

class P2pNavigator extends StatelessWidget {
  final GlobalKey<NavigatorState> navigatorKey;

  const P2pNavigator({super.key, required this.navigatorKey});

  @override
  Widget build(BuildContext context) {
    return Navigator(
      key: navigatorKey,
      onGenerateRoute: (settings) {
        return MaterialPageRoute<void>(
          settings: settings,
          builder: (_) => const P2pHomeScreen(),
        );
      },
    );
  }
}

