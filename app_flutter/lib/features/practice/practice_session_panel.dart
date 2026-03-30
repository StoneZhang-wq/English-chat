import 'package:flutter/material.dart';

import '../../core/theme/echo_theme.dart';

class PracticeSessionPanel extends StatefulWidget {
  final String scenarioTitle;
  const PracticeSessionPanel({super.key, required this.scenarioTitle});

  @override
  State<PracticeSessionPanel> createState() => _PracticeSessionPanelState();
}

class _PracticeSessionPanelState extends State<PracticeSessionPanel> {
  final _controller = TextEditingController();
  final List<_Msg> _messages = [];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _sendText() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    setState(() {
      _messages.add(_Msg(isUser: true, text: text));
      _controller.clear();
      // TODO: 对接 backend + 端侧 ASR 后替换为真实回复
      _messages.add(_Msg(isUser: false, text: '（占位）收到：$text'));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: echoTaskYellow,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: echoTaskYellowBorder),
          ),
          child: Row(
            children: [
              Text(
                'CURRENT TASK:',
                style: Theme.of(context)
                    .textTheme
                    .labelSmall
                    ?.copyWith(color: echoMuted),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  widget.scenarioTitle.isEmpty
                      ? 'Practice in this scenario.'
                      : widget.scenarioTitle,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              color: echoSurface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: echoBorder),
            ),
            child: _messages.isEmpty
                ? Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      '输入文字后发送；或后续长按麦克风说话，松手发送、上滑取消。',
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: echoMuted),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _messages.length,
                    itemBuilder: (context, i) => _Bubble(msg: _messages[i]),
                  ),
          ),
        ),
        const SizedBox(height: 10),
        _InputBar(
          controller: _controller,
          onSend: _sendText,
        ),
      ],
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  const _InputBar({required this.controller, required this.onSend});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            minLines: 1,
            maxLines: 4,
            decoration: InputDecoration(
              hintText: 'Type a message…',
              filled: true,
              fillColor: echoSurface,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide(color: echoBorder),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide(color: echoBorder),
              ),
            ),
            onSubmitted: (_) => onSend(),
          ),
        ),
        const SizedBox(width: 10),
        Container(
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: Color(0xFF4CAF50),
          ),
          child: IconButton(
            onPressed: onSend,
            icon: const Icon(Icons.send, color: Colors.white),
            tooltip: 'Send',
          ),
        ),
      ],
    );
  }
}

class _Bubble extends StatelessWidget {
  final _Msg msg;
  const _Bubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final bg = msg.isUser ? const Color(0xFF4CAF50) : echoBackground;
    final fg = msg.isUser ? Colors.white : echoOnBackground;
    final align = msg.isUser ? Alignment.centerRight : Alignment.centerLeft;
    final radius = BorderRadius.circular(14);

    return Align(
      alignment: align,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        constraints: const BoxConstraints(maxWidth: 320),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: radius,
          border: msg.isUser ? null : Border.all(color: echoBorder),
        ),
        child: Text(
          msg.text,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: fg),
        ),
      ),
    );
  }
}

class _Msg {
  final bool isUser;
  final String text;
  _Msg({required this.isUser, required this.text});
}

