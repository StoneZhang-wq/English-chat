import 'package:flutter/material.dart';

// EchoEnglish 风格：浅底、黑字、细边框（对齐 Kotlin Color.kt）
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

const _echoSurfaceVariant = Color(0xFFF0F0EF);

/// 左上角 Logo：浅灰斜体衬线（对齐 Kotlin TypographyLogo）
const echoTypographyLogo = TextStyle(
  fontFamily: 'serif',
  fontStyle: FontStyle.italic,
  fontWeight: FontWeight.normal,
  fontSize: 18,
  height: 22 / 18,
  color: echoMuted,
);

/// P2P 主标题：衬线斜体（对齐 Kotlin TypographyP2pTitle）
const echoTypographyP2pTitle = TextStyle(
  fontFamily: 'serif',
  fontStyle: FontStyle.italic,
  fontWeight: FontWeight.normal,
  fontSize: 28,
  height: 34 / 28,
  color: echoOnBackground,
);

/// 对齐 Kotlin Type.kt + Theme.kt 的 EchoLightColorScheme / Typography
ThemeData buildEchoTheme() {
  const serif = 'serif';
  const sans = 'sans-serif';

  final textTheme = const TextTheme(
    displayLarge: TextStyle(
      fontFamily: serif,
      fontWeight: FontWeight.w400,
      fontSize: 34,
      height: 40 / 34,
      letterSpacing: -0.5,
    ),
    headlineLarge: TextStyle(
      fontFamily: serif,
      fontWeight: FontWeight.w400,
      fontSize: 30,
      height: 36 / 30,
    ),
    headlineMedium: TextStyle(
      fontFamily: serif,
      fontWeight: FontWeight.w400,
      fontSize: 26,
      height: 32 / 26,
    ),
    headlineSmall: TextStyle(
      fontFamily: serif,
      fontWeight: FontWeight.w400,
      fontSize: 24,
      height: 30 / 24,
    ),
    titleLarge: TextStyle(
      fontFamily: serif,
      fontWeight: FontWeight.w400,
      fontSize: 22,
      height: 28 / 22,
    ),
    titleMedium: TextStyle(
      fontFamily: sans,
      fontWeight: FontWeight.w600,
      fontSize: 16,
      height: 22 / 16,
    ),
    bodyLarge: TextStyle(
      fontFamily: sans,
      fontWeight: FontWeight.w400,
      fontSize: 15,
      height: 22 / 15,
    ),
    bodyMedium: TextStyle(
      fontFamily: sans,
      fontWeight: FontWeight.w400,
      fontSize: 14,
      height: 20 / 14,
    ),
    bodySmall: TextStyle(
      fontFamily: sans,
      fontWeight: FontWeight.w400,
      fontSize: 12,
      height: 17 / 12,
    ),
    labelSmall: TextStyle(
      fontFamily: sans,
      fontWeight: FontWeight.w500,
      fontSize: 10,
      height: 14 / 10,
      letterSpacing: 0.8,
    ),
    labelMedium: TextStyle(
      fontFamily: sans,
      fontWeight: FontWeight.w600,
      fontSize: 11,
      height: 14 / 11,
      letterSpacing: 0.6,
    ),
  ).apply(
    bodyColor: echoOnBackground,
    displayColor: echoOnBackground,
  );

  final colorScheme = ColorScheme.light(
    primary: echoOnBackground,
    onPrimary: Colors.white,
    primaryContainer: echoNavSelectedCircle,
    onPrimaryContainer: echoOnBackground,
    secondary: echoMuted,
    onSecondary: echoOnBackground,
    surface: echoSurface,
    onSurface: echoOnBackground,
    surfaceContainerHighest: _echoSurfaceVariant,
    onSurfaceVariant: echoMuted,
    outline: echoBorder,
    outlineVariant: echoBorder,
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: echoBackground,
    textTheme: textTheme,
    dividerColor: echoBorder,
    appBarTheme: const AppBarTheme(
      backgroundColor: echoBackground,
      foregroundColor: echoOnBackground,
      elevation: 0,
      scrolledUnderElevation: 0,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: echoSurface,
      indicatorColor: echoNavSelectedCircle,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (s) => textTheme.labelSmall?.copyWith(
          fontWeight: s.contains(WidgetState.selected)
              ? FontWeight.bold
              : FontWeight.w500,
        ),
      ),
    ),
  );
}
