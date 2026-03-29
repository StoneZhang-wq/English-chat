package com.example.englishchat.media

import java.io.File
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** 与 [PracticeAudioRecorder] 一致：16kHz、单声道、16-bit LE */
private const val PRACTICE_WAV_SAMPLE_RATE = 16_000

/** [PracticeAudioRecorder.writeWavFile] 固定为 44 字节 WAV 头 + `data` PCM，无其它 chunk。*/
private const val PRACTICE_WAV_HEADER_BYTES = 44L

/**
 * 直接用文件总长减固定头长度推算时长（最快、与自写文件格式严格一致）。
 */
fun practiceRecordedWavDurationMsFromOurFile(file: File): Long? {
    val pcmBytes = file.length() - PRACTICE_WAV_HEADER_BYTES
    if (pcmBytes <= 0L) return null
    return (pcmBytes / 2L) * 1000L / PRACTICE_WAV_SAMPLE_RATE
}

/**
 * 从 RIFF/WAV 的 `data` 块长度推算播放时长（毫秒）。
 * 不依赖 [android.media.MediaMetadataRetriever]，避免部分机型对 WAV 误报时长。
 */
fun practiceRecordedWavDurationMs(path: String): Long? {
    return runCatching {
        FileInputStream(path).use { ins ->
            val riff = ByteArray(12)
            if (ins.read(riff) != 12) return null
            if (!byteTag(riff, 0, "RIFF") || !byteTag(riff, 8, "WAVE")) return null
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
                        val samples = chunkSize / 2L
                        return (samples * 1000L) / PRACTICE_WAV_SAMPLE_RATE
                    }
                    else -> skipChunk(ins, chunkSize)
                }
            }
            null
        }
    }.getOrNull()
}

private fun byteTag(arr: ByteArray, offset: Int, tag: String): Boolean {
    if (offset + 4 > arr.size) return false
    return tag.toByteArray(Charsets.US_ASCII).contentEquals(arr.copyOfRange(offset, offset + 4))
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
