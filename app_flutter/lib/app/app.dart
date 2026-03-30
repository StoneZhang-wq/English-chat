import 'package:flutter/material.dart';

import '../features/home/home_screen.dart';

class MyEnglishChatApp extends StatelessWidget {
  const MyEnglishChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MyEnglishChat',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF4CAF50)),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

