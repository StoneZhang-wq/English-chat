package com.example.englishchat.media

import android.content.Context
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.concurrent.thread

/**
 * 练习页短录音：16kHz 单声道 PCM，封装为 WAV，供离线 ASR（Vosk）与 [MediaPlayer] 播放。
 */
class PracticeAudioRecorder(private val context: Context) {

    private var audioRecord: AudioRecord? = null
    private var recordThread: Thread? = null

    @Volatile
    private var shouldCapture = false

    private val pcmStream = ByteArrayOutputStream()
    private var outputFile: File? = null

    fun start(): File {
        cancel()
        val file = File(context.cacheDir, "practice_${System.currentTimeMillis()}.wav")
        outputFile = file
        pcmStream.reset()

        val minBuf = AudioRecord.getMinBufferSize(
            SAMPLE_RATE_HZ,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        require(minBuf > 0) { "AudioRecord not supported on this device" }

        // VOICE_RECOGNITION 在真机/模拟器上往往比 MIC 更适合语音（增益与预处理）
        val recorder = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            SAMPLE_RATE_HZ,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            minBuf * 2,
        )
        audioRecord = recorder
        shouldCapture = true
        recorder.startRecording()

        recordThread = thread(name = "practice-wav") {
            // 等到真正进入录音态，避免前几帧全 0
            var wait = 0
            while (
                recorder.recordingState != AudioRecord.RECORDSTATE_RECORDING &&
                wait < 50
            ) {
                Thread.sleep(10)
                wait++
            }
            val buf = ByteArray(minBuf)
            while (shouldCapture) {
                val n = recorder.read(buf, 0, buf.size)
                when {
                    n > 0 -> pcmStream.write(buf, 0, n)
                    n == 0 -> { /* 偶发，继续 */ }
                    else -> Log.w(TAG, "AudioRecord.read error code=$n")
                }
            }
            // 耗尽缓冲区，避免尾音被截断
            while (true) {
                val n = recorder.read(buf, 0, buf.size)
                when {
                    n > 0 -> pcmStream.write(buf, 0, n)
                    n <= 0 -> break
                }
            }
        }
        return file
    }

    /**
     * 立即停止采集 PCM（请在主线程尽早调用，再在后台线程调用 [stop]）。
     * 若仅在异步 [stop] 里才把 [shouldCapture] 置 false，协程排队期间会持续录音，文件易多出一大段静音、
     * 时长与体感相差甚远。
     */
    fun signalStopCapture() {
        shouldCapture = false
    }

    /** @return 录音文件；未开始或失败则为 null */
    fun stop(): File? {
        shouldCapture = false
        recordThread?.join(10_000L)
        recordThread = null

        try {
            audioRecord?.stop()
        } catch (_: Exception) {
        }
        try {
            audioRecord?.release()
        } catch (_: Exception) {
        }
        audioRecord = null

        val file = outputFile
        outputFile = null
        val pcm = pcmStream.toByteArray()
        pcmStream.reset()
        if (file == null || pcm.isEmpty()) {
            Log.w(TAG, "stop: empty pcm or no file")
            return null
        }
        Log.d(TAG, "stop: pcm bytes=${pcm.size} (~${pcm.size / 2.0 / SAMPLE_RATE_HZ}s)")
        writeWavFile(file, pcm)
        return file.takeIf { it.exists() && it.length() > 0L }
    }

    fun cancel() {
        shouldCapture = false
        recordThread?.join(10_000L)
        recordThread = null
        try {
            audioRecord?.stop()
        } catch (_: Exception) {
        }
        try {
            audioRecord?.release()
        } catch (_: Exception) {
        }
        audioRecord = null
        pcmStream.reset()
        outputFile?.delete()
        outputFile = null
    }

    private fun writeWavFile(file: File, pcm: ByteArray) {
        val channels = 1
        val bitsPerSample = 16
        val byteRate = SAMPLE_RATE_HZ * channels * bitsPerSample / 8
        val blockAlign = (channels * bitsPerSample / 8).toShort()
        val dataSize = pcm.size
        val riffPayloadSize = 36 + dataSize

        val buf = ByteBuffer.allocate(44 + pcm.size).order(ByteOrder.LITTLE_ENDIAN)
        buf.put("RIFF".toByteArray(Charsets.US_ASCII))
        buf.putInt(riffPayloadSize)
        buf.put("WAVE".toByteArray(Charsets.US_ASCII))
        buf.put("fmt ".toByteArray(Charsets.US_ASCII))
        buf.putInt(16)
        buf.putShort(1)
        buf.putShort(channels.toShort())
        buf.putInt(SAMPLE_RATE_HZ)
        buf.putInt(byteRate)
        buf.putShort(blockAlign)
        buf.putShort(bitsPerSample.toShort())
        buf.put("data".toByteArray(Charsets.US_ASCII))
        buf.putInt(dataSize)
        buf.put(pcm)
        file.writeBytes(buf.array())
    }

    companion object {
        private const val TAG = "PracticeAudioRecorder"
        private const val SAMPLE_RATE_HZ = 16_000
    }
}
