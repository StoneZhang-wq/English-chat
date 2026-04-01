import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../app/widgets/echo_bottom_bar.dart';
import '../../../app/widgets/echo_top_bar.dart';
import '../../learn/presentation/learn_navigator.dart';
import '../../p2p_match/presentation/p2p_navigator.dart';
import '../../profile/presentation/profile_home_screen.dart';
import '../../voice_lab/presentation/voice_lab_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final GlobalKey<NavigatorState> _learnNavKey = GlobalKey<NavigatorState>();
  final GlobalKey<NavigatorState> _p2pNavKey = GlobalKey<NavigatorState>();

  /// 产品底栏：`learn` / `p2p_match` / `profile`
  String _route = 'learn';

  void _onBottomNavigate(String route) {
    setState(() => _route = route);
  }

  int get _stackIndex {
    switch (_route) {
      case 'p2p_match':
        return 1;
      case 'profile':
        return 2;
      case 'learn':
      default:
        return 0;
    }
  }

  void _handleSystemBack(bool didPop, dynamic result) {
    if (didPop) return;
    if (_stackIndex == 0) {
      final nav = _learnNavKey.currentState;
      if (nav != null && nav.canPop()) {
        nav.pop();
        return;
      }
    } else if (_stackIndex == 1) {
      final nav = _p2pNavKey.currentState;
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
              EchoTopBar(
                onOpenVoiceLab: () {
                  Navigator.of(context).push<void>(
                    MaterialPageRoute<void>(
                      builder: (_) => const VoiceLabScreen(),
                    ),
                  );
                },
              ),
              Expanded(
                child: IndexedStack(
                  index: _stackIndex,
                  children: [
                    LearnNavigator(navigatorKey: _learnNavKey),
                    P2pNavigator(navigatorKey: _p2pNavKey),
                    const ProfileHomeScreen(),
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
