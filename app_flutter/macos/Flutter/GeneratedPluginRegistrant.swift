//
//  Generated file. Do not edit.
//

import FlutterMacOS
import Foundation

import audio_session
import flutter_kitten_tts
import flutter_onnxruntime
import flutter_tts
import just_audio
import record_macos

func RegisterGeneratedPlugins(registry: FlutterPluginRegistry) {
  AudioSessionPlugin.register(with: registry.registrar(forPlugin: "AudioSessionPlugin"))
  KittenTtsFlutterPlugin.register(with: registry.registrar(forPlugin: "KittenTtsFlutterPlugin"))
  FlutterOnnxruntimePlugin.register(with: registry.registrar(forPlugin: "FlutterOnnxruntimePlugin"))
  FlutterTtsPlugin.register(with: registry.registrar(forPlugin: "FlutterTtsPlugin"))
  JustAudioPlugin.register(with: registry.registrar(forPlugin: "JustAudioPlugin"))
  RecordMacOsPlugin.register(with: registry.registrar(forPlugin: "RecordMacOsPlugin"))
}
