/// 对齐 backend `PracticeChatRequest` / `ChatMessage` / `PracticeChatResponse`
class ChatMessageDto {
  final String role;
  final String content;

  const ChatMessageDto({
    required this.role,
    required this.content,
  });

  Map<String, dynamic> toJson() => {
        'role': role,
        'content': content,
      };
}

class PracticeChatRequest {
  final List<ChatMessageDto> messages;
  final String? scenarioTitle;

  const PracticeChatRequest({
    required this.messages,
    this.scenarioTitle,
  });

  Map<String, dynamic> toJson() => {
        'messages': messages.map((e) => e.toJson()).toList(),
        if (scenarioTitle != null && scenarioTitle!.isNotEmpty)
          'scenario_title': scenarioTitle,
      };
}

class PracticeChatResponse {
  final String reply;

  const PracticeChatResponse({required this.reply});

  factory PracticeChatResponse.fromJson(Map<String, dynamic> json) {
    final r = json['reply'];
    if (r is! String) {
      throw FormatException('reply 字段缺失或类型错误');
    }
    return PracticeChatResponse(reply: r);
  }
}
