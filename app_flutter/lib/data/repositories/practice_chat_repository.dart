import 'package:dio/dio.dart';

import '../dto/practice_chat_dto.dart';
import '../http/dio_client.dart';

/// 对接 FastAPI `POST /api/practice/chat`（豆包/OpenAI 兼容，密钥仅在 backend）
class PracticeChatRepository {
  PracticeChatRepository({Dio? dio}) : _dio = dio ?? DioClient.create();

  final Dio _dio;

  Future<String> sendChat({
    required List<ChatMessageDto> messages,
    String? scenarioTitle,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        'api/practice/chat',
        data: PracticeChatRequest(
          messages: messages,
          scenarioTitle: scenarioTitle,
        ).toJson(),
      );

      final data = res.data;
      if (data == null) {
        throw StateError('服务器返回空 body');
      }
      return PracticeChatResponse.fromJson(data).reply;
    } on DioException catch (e) {
      final body = e.response?.data;
      if (body is Map && body['detail'] != null) {
        final d = body['detail'];
        if (d is String) throw Exception(d);
        if (d is List && d.isNotEmpty) throw Exception('$d');
      }
      throw Exception(e.message ?? '网络错误');
    }
  }
}
