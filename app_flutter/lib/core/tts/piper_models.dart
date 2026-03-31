import 'package:runanywhere/runanywhere.dart';
import 'package:runanywhere_onnx/runanywhere_onnx.dart';

/// Piper voices registry (ONNX / tar.gz artifacts).
///
/// 注意：这里只注册“可用 voice”，不强制下载；下载发生在第一次使用时。
abstract final class PiperModels {
  static const amyMediumId = 'piper-amy-medium';
  static const lessacMediumId = 'piper-lessac-medium';

  static void register() {
    // Piper Amy (US English) - medium quality
    Onnx.addModel(
      id: amyMediumId,
      name: 'Piper Amy (English, US)',
      url:
          'https://github.com/RunanywhereAI/sherpa-onnx/releases/download/runanywhere-models-v1/vits-piper-en_US-amy-medium.tar.gz',
      modality: ModelCategory.speechSynthesis,
      memoryRequirement: 50 * 1000 * 1000,
    );

    // Piper Lessac (US English) - medium quality
    Onnx.addModel(
      id: lessacMediumId,
      name: 'Piper Lessac (English, US)',
      url:
          'https://github.com/RunanywhereAI/sherpa-onnx/releases/download/runanywhere-models-v1/vits-piper-en_US-lessac-medium.tar.gz',
      modality: ModelCategory.speechSynthesis,
      memoryRequirement: 65 * 1000 * 1000,
    );
  }
}

