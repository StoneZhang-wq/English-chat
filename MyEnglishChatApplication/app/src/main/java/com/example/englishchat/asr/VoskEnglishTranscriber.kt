package com.example.englishchat.asr

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.vosk.Model
import org.vosk.Recognizer
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * 使用 Vosk small 英文模型对 **16kHz 单声道 16-bit LE PCM** WAV 做离线转写。
 * 从 WAV 中解析 `data` 块（不假设固定 44 字节头）。
 */
object VoskEnglishTranscriber {

    private const val TAG = "VoskEnglishTranscriber"
    private const val SAMPLE_RATE = 16000.0f
    /** 与 Kaldi/Vosk 常用 10ms 帧（160 样点 * 2 字节 = 320 字节）对齐，避免 acceptWaveForm 块错位。 */
    private const val CHUNK = 6400

    @Volatile
    private var cachedModel: Model? = null

    private fun getModel(context: Context): Model {
        cachedModel?.let { return it }
        synchronized(this) {
            cachedModel?.let { return it }
            val path = VoskModelManager.modelDirectory(context).absolutePath
            Log.d(TAG, "loading Vosk model from $path")
            val m = Model(path)
            cachedModel = m
            return m
        }
    }

    /** 释放模型（例如单元测试或设置里「清除模型」时可调）。 */
    fun releaseModel() {
        synchronized(this) {
            runCatching { cachedModel?.close() }
            cachedModel = null
        }
    }

    /**
     * 转写 WAV 文件；在后台线程执行。
     * 注意：**当前模型为英文 small**，说中文时常得到空串；请尽量清晰说英文。
     */
    suspend fun transcribe(context: Context, wavPath: String): String =
        withContext(Dispatchers.IO) {
            val pcm = extractPcmFromWav(wavPath)
            if (pcm == null || pcm.isEmpty()) {
                Log.w(TAG, "no PCM extracted from $wavPath")
                return@withContext ""
            }
            val durSec = pcm.size / 2.0 / SAMPLE_RATE
            logPcmSignalLevel(pcm)
            Log.d(TAG, "pcm bytes=${pcm.size} (~$durSec s @16k mono)")

            val model = getModel(context)
            val recognizer = Recognizer(model, SAMPLE_RATE)
            try {
                var offset = 0
                while (offset < pcm.size) {
                    val len = minOf(CHUNK, pcm.size - offset)
                    val evenLen = len - (len % 2)
                    if (evenLen > 0) {
                        val slice = pcm.copyOfRange(offset, offset + evenLen)
                        if (recognizer.acceptWaveForm(slice, slice.size)) {
                            val mid = runCatching { recognizer.getResult() }.getOrNull()
                            Log.d(TAG, "acceptWaveForm endpoint; result=$mid")
                        }
                    }
                    offset += len
                }
                val json = recognizer.getFinalResult()
                val text = parseText(json)
                if (text.isBlank()) {
                    Log.w(
                        TAG,
                        "empty text; final=$json partial=${recognizer.getPartialResult()} " +
                            "(英文模型对中文/静音环境常无输出)",
                    )
                }
                text
            } finally {
                recognizer.close()
            }
        }

    /** 统计 16-bit LE 单声道 PCM 峰值；若 maxAbs<200 多半是模拟器静音或未接麦克风。 */
    private fun logPcmSignalLevel(pcm: ByteArray) {
        if (pcm.size < 2) return
        val bb = ByteBuffer.wrap(pcm).order(ByteOrder.LITTLE_ENDIAN)
        var maxAbs = 0
        val sampleCount = minOf(50_000, pcm.size / 2)
        var i = 0
        while (i < sampleCount && bb.remaining() >= 2) {
            val s = bb.short.toInt()
            val v = kotlin.math.abs(s)
            if (v > maxAbs) maxAbs = v
            i++
        }
        Log.d(TAG, "pcm peak |sample| (first ~$sampleCount samples) max=$maxAbs (typ. speech often >2000)")
    }

    /** 解析 RIFF/WAVE，返回 `data` 块原始 PCM；sample 数为偶数（16-bit 对齐）。 */
    private fun extractPcmFromWav(path: String): ByteArray? {
        FileInputStream(path).use { ins ->
            val riff = ByteArray(12)
            if (ins.read(riff) != 12) return null
            if (!byteTag(riff, 0, "RIFF") || !byteTag(riff, 8, "WAVE")) {
                Log.w(TAG, "not a RIFF/WAVE file")
                return null
            }
            val four = ByteArray(4)
            while (ins.read(four) == 4) {
                val id = String(four, Charsets.US_ASCII)
                val sizeBuf = ByteArray(4)
                if (ins.read(sizeBuf) != 4) return null
                val chunkSize = ByteBuffer.wrap(sizeBuf).order(ByteOrder.LITTLE_ENDIAN).int
                when (id) {
                    "fmt ", "LIST", "fact", "PEAK", "labl", "note" -> skipChunk(ins, chunkSize)
                    "data" -> {
                        if (chunkSize <= 0) return null
                        val data = ByteArray(chunkSize)
                        var r = 0
                        while (r < chunkSize) {
                            val n = ins.read(data, r, chunkSize - r)
                            if (n < 0) return null
                            r += n
                        }
                        return if (data.isEmpty()) {
                            null
                        } else if (data.size % 2 == 1) {
                            data.copyOf(data.size - 1)
                        } else {
                            data
                        }
                    }
                    else -> skipChunk(ins, chunkSize)
                }
            }
        }
        return null
    }

    private fun skipChunk(ins: FileInputStream, size: Int) {
        var left = size.toLong()
        val buf = ByteArray(8192)
        while (left > 0) {
            val n = ins.read(buf, 0, minOf(buf.size.toLong(), left).toInt())
            if (n <= 0) break
            left -= n
        }
        if (size % 2 == 1) ins.read()
    }

    private fun byteTag(arr: ByteArray, offset: Int, tag: String): Boolean {
        if (offset + 4 > arr.size) return false
        return tag.toByteArray(Charsets.US_ASCII).contentEquals(arr.copyOfRange(offset, offset + 4))
    }

    private fun parseText(json: String): String {
        return runCatching {
            JSONObject(json).optString("text", "").trim()
        }.getOrElse {
            Log.w(TAG, "parse result failed: $json")
            ""
        }
    }
}
