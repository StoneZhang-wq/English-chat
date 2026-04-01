import 'dart:convert';

/// Vosk 返回 JSON 字符串，常见字段为 [text]（句末）或 [partial]（中间结果）。
String extractVoskDisplayText(String raw) {
  final s = raw.trim();
  if (s.isEmpty) return '';
  try {
    final decoded = jsonDecode(s);
    if (decoded is Map<String, dynamic>) {
      final text = decoded['text'];
      if (text is String && text.isNotEmpty) return text;
      final partial = decoded['partial'];
      if (partial is String) return partial;
    }
  } catch (_) {
    return s;
  }
  return s;
}
