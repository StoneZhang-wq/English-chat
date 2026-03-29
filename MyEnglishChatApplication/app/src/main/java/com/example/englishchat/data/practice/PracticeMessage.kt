package com.example.englishchat.data.practice

/**
 * Practice 会话消息：纯文字或语音（本地录音文件 + 转写文案；AI 语音可为 TTS 合成）。
 */
sealed class PracticeMessage {
    abstract val id: Long
    abstract val isUser: Boolean

    data class Text(
        override val id: Long,
        override val isUser: Boolean,
        val body: String,
    ) : PracticeMessage()

    /**
     * @param audioPath 用户录音绝对路径；AI 占位语音可为空，播放走 TTS
     * @param isAiTts AI 侧无录音文件时 true，播放用 TextToSpeech 朗读 [transcript]
     */
    data class Voice(
        override val id: Long,
        override val isUser: Boolean,
        val audioPath: String,
        val durationMs: Long,
        val transcript: String,
        val isAiTts: Boolean = false,
    ) : PracticeMessage()
}

/**
 * 语音气泡上的展开/翻译/优化 UI 状态（按消息 id 存于 remember）。
 */
data class VoiceBubbleUiState(
    val expanded: Boolean = false,
    val translationVisible: Boolean = false,
    val translatedText: String? = null,
    val optimizedSectionVisible: Boolean = false,
    val optimizedText: String? = null,
)
