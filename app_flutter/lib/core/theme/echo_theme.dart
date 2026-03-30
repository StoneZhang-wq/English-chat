import 'package:flutter/material.dart';

// EchoEnglish 风格：浅底、黑字、细边框（对齐 Kotlin 端 Color.kt）
const echoBackground = Color(0xFFF5F5F4);
const echoSurface = Color(0xFFFFFFFF);
const echoOnBackground = Color(0xFF1A1A1A);
const echoMuted = Color(0xFF8A8A8A);
const echoBorder = Color(0xFFE5E5E5);
const echoNavSelectedCircle = Color(0xFFEBEBEB);
const echoSubtitleCaps = Color(0xFF9CA3AF);
const echoDialogueGreen = Color(0xFF2F5F4A);
const echoTaskYellow = Color(0xFFFFF8E6);
const echoTaskYellowBorder = Color(0xFFF5E6B8);

ThemeData buildEchoTheme() {
  final colorScheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF4CAF50),
    brightness: Brightness.light,
    surface: echoSurface,
  );

  final base = ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: echoBackground,
  );

  return base.copyWith(
    dividerColor: echoBorder,
    appBarTheme: const AppBarTheme(
      backgroundColor: echoBackground,
      foregroundColor: echoOnBackground,
      elevation: 0,
    ),
    textTheme: base.textTheme.apply(
      bodyColor: echoOnBackground,
      displayColor: echoOnBackground,
    ),
  );
}

