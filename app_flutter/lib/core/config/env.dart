enum AppEnv { dev, prod }

class Env {
  static const AppEnv current = AppEnv.dev;

  /// Development backend base URL:
  /// - Android emulator: http://10.0.2.2:8088/
  /// - iOS simulator:    http://127.0.0.1:8088/
  /// - Real device:      http://PC_LAN_IP:8088/
  static const String devBackendBaseUrl = String.fromEnvironment(
    'BACKEND_BASE_URL',
    defaultValue: 'http://10.0.2.2:8088/',
  );

  /// Production backend base URL (set at build time)
  static const String prodBackendBaseUrl = String.fromEnvironment(
    'BACKEND_BASE_URL',
    defaultValue: 'https://example.com/',
  );

  static String get backendBaseUrl {
    final url = current == AppEnv.dev ? devBackendBaseUrl : prodBackendBaseUrl;
    return url.endsWith('/') ? url : '$url/';
  }
}

