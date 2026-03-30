import 'package:flutter/material.dart';

import '../shadowing/shadowing_home_screen.dart';
import '../practice/practice_home_screen.dart';
import '../p2p/p2p_home_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('MyEnglishChat')),
      body: IndexedStack(
        index: _index,
        children: const [
          ShadowingHomeScreen(),
          PracticeHomeScreen(),
          P2pHomeScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.headphones),
            label: 'Shadowing',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline),
            label: 'Practice',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_alt_outlined),
            label: 'P2P',
          ),
        ],
      ),
    );
  }
}

