import 'package:dio/dio.dart';

import '../../core/config/env.dart';

class DioClient {
  DioClient._();

  static Dio create() {
    final dio = Dio(
      BaseOptions(
        baseUrl: Env.backendBaseUrl,
        connectTimeout: const Duration(seconds: 20),
        receiveTimeout: const Duration(seconds: 60),
        sendTimeout: const Duration(seconds: 60),
        headers: const {'Content-Type': 'application/json'},
      ),
    );
    return dio;
  }
}

