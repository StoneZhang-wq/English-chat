enum AppEnv { dev, prod }

class Env {
  static const AppEnv current = AppEnv.dev;

  /// Development backend base URL（填 **跑 FastAPI 的电脑** 的局域网 IP，不是手机 IP）：
  /// - 当前默认：`192.168.0.59` → `http://192.168.0.59:8088/`（真机与同网开发机联调）
  /// - Android 模拟器访问本机：若 `.59` 不通，请用
  ///   `--dart-define=BACKEND_BASE_URL=http://10.0.2.2:8088/`
  /// - iOS 模拟器：`http://127.0.0.1:8088/`
  /// 任意环境可用 `--dart-define=BACKEND_BASE_URL=...` 覆盖（Android Studio：Run 配置 Additional args）
  static const String devBackendBaseUrl = String.fromEnvironment(
    'BACKEND_BASE_URL',
    defaultValue: 'http://192.168.0.59:8088/',
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

