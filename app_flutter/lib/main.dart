import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:runanywhere/runanywhere.dart';
import 'package:runanywhere_onnx/runanywhere_onnx.dart';

import 'app/app.dart';
import 'core/tts/piper_models.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await RunAnywhere.initialize();
  await Onnx.register();
  PiperModels.register();
  runApp(const ProviderScope(child: MyEnglishChatApp()));
}

