import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../app/widgets/echo_bottom_bar.dart';
import '../../../app/widgets/echo_top_bar.dart';
import '../../ai_dialogue/presentation/ai_dialogue_home_screen.dart';
import '../../p2p/presentation/p2p_home_screen.dart';
import '../../shadowing/presentation/shadowing_tab_navigator.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final GlobalKey<NavigatorState> _shadowingNavKey = GlobalKey<NavigatorState>();

  /// 与 Kotlin `AppRoute` 一致：`shadowing` / `ai_dialogue` / `p2p`
  String _route = 'shadowing';

  void _onBottomNavigate(String route) {
    setState(() => _route = route);
  }

  int get _stackIndex {
    switch (_route) {
      case 'ai_dialogue':
        return 1;
      case 'p2p':
        return 2;
      case 'shadowing':
      default:
        return 0;
    }
  }

  void _handleSystemBack(bool didPop, dynamic result) {
    if (didPop) return;
    if (_stackIndex == 0) {
      final nav = _shadowingNavKey.currentState;
      if (nav != null && nav.canPop()) {
        nav.pop();
        return;
      }
    }
    SystemNavigator.pop();
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: _handleSystemBack,
      child: Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              const EchoTopBar(),
              Expanded(
                child: IndexedStack(
                  index: _stackIndex,
                  children: [
                    ShadowingTabNavigator(navigatorKey: _shadowingNavKey),
                    const AiDialogueHomeScreen(),
                    const P2pHomeScreen(),
                  ],
                ),
              ),
              EchoBottomBar(
                currentRoute: _route,
                onNavigate: _onBottomNavigate,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
