import 'package:flutter/material.dart';

import '../core/theme/echo_theme.dart';
import '../features/home/home_screen.dart';

class MyEnglishChatApp extends StatelessWidget {
  const MyEnglishChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MyEnglishChat',
      theme: buildEchoTheme(),
      home: const HomeScreen(),
    );
  }
}

