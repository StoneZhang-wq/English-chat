package com.example.englishchat.media

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

/**
 * 应用内共享的英语朗读（系统 [TextToSpeech]），供 Practice / Shadowing 等复用。
 * 须在主线程创建；由界面层 [remember] 持有，在离开场景时 [shutdown]。
 */
class PracticeTextToSpeech(context: Context) {
    private val appContext = context.applicationContext
    private var engine: TextToSpeech? = null

    /** 引擎初始化成功后为 true */
    var isReady: Boolean = false
        private set

    /**
     * 创建引擎并在就绪时回调（可多次调用，仅首次真正初始化）。
     */
    fun initialize(onReady: (Boolean) -> Unit = {}) {
        if (engine != null) {
            onReady(isReady)
            return
        }
        engine = TextToSpeech(appContext) { status ->
            isReady = status == TextToSpeech.SUCCESS
            if (isReady) {
                engine?.language = Locale.US
            }
            onReady(isReady)
        }
    }

    /**
     * 朗读整段文本（会打断当前朗读）。
     */
    fun speak(text: String, utteranceId: String) {
        if (!isReady || text.isBlank()) return
        engine?.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)
    }

    /**
     * 按顺序朗读多句（第一句 FLUSH，后续 ADD）。
     */
    fun speakQueued(lines: List<String>, utteranceIdPrefix: String) {
        if (!isReady) return
        val parts = lines.map { it.trim() }.filter { it.isNotEmpty() }
        if (parts.isEmpty()) return
        parts.forEachIndexed { index, line ->
            val mode = if (index == 0) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD
            engine?.speak(line, mode, null, "${utteranceIdPrefix}_$index")
        }
    }

    fun stop() {
        engine?.stop()
    }

    fun shutdown() {
        engine?.stop()
        engine?.shutdown()
        engine = null
        isReady = false
    }
}
