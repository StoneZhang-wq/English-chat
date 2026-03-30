import 'package:flutter/material.dart';

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
          _TabPlaceholder(title: 'Shadowing'),
          _TabPlaceholder(title: 'Practice'),
          _TabPlaceholder(title: 'P2P'),
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

class _TabPlaceholder extends StatelessWidget {
  final String title;
  const _TabPlaceholder({required this.title});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        '$title（Flutter 骨架已就绪，功能迁移中）',
        style: Theme.of(context).textTheme.titleMedium,
        textAlign: TextAlign.center,
      ),
    );
  }
}

