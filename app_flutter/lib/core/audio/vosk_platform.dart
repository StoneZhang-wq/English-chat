import 'package:flutter/foundation.dart';

/// [vosk_flutter_service] 在 **Android / iOS** 上通过原生通道提供麦克风流式识别。
bool get isVoskSttSupported {
  if (kIsWeb) return false;
  return defaultTargetPlatform == TargetPlatform.android ||
      defaultTargetPlatform == TargetPlatform.iOS ||
      defaultTargetPlatform == TargetPlatform.linux ||
      defaultTargetPlatform == TargetPlatform.windows ||
      defaultTargetPlatform == TargetPlatform.macOS;
}

/// 麦克风流（[SpeechService]）在移动双端可用。
bool get isVoskMicStreamingSupported {
  if (kIsWeb) return false;
  return defaultTargetPlatform == TargetPlatform.android ||
      defaultTargetPlatform == TargetPlatform.iOS;
}
