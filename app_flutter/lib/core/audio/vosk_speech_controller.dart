// Web 不编译带 FFI 的 Vosk 实现；见 vosk_speech_controller_io / vosk_speech_controller_stub。
export 'vosk_speech_controller_stub.dart'
    if (dart.library.io) 'vosk_speech_controller_io.dart';
