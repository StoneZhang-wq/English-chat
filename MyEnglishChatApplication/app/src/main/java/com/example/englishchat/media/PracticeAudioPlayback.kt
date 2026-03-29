package com.example.englishchat.media

import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log
import java.io.File
import java.util.concurrent.atomic.AtomicReference

/** 播放用户本地录音文件（WAV / m4a 等）。异步 prepare；释放前 reset + 清空监听，避免 “mediaplayer went away with unhandled events”。 */
object PracticeAudioPlayback {

    private const val TAG = "PracticeAudioPlayback"

    private val mediaPlayerRef = AtomicReference<MediaPlayer?>(null)

    private fun releaseMediaPlayer(mp: MediaPlayer) {
        runCatching {
            mp.setOnPreparedListener(null)
            mp.setOnCompletionListener(null)
            mp.setOnErrorListener(null)
            runCatching {
                if (mp.isPlaying) mp.stop()
            }
            mp.reset()
            mp.release()
        }
    }

    fun playFile(
        path: String,
        onComplete: () -> Unit,
    ) {
        stop()
        val file = File(path)
        if (!file.exists() || !file.canRead() || file.length() == 0L) {
            Log.w(TAG, "playFile: invalid file path=$path exists=${file.exists()} len=${if (file.exists()) file.length() else -1}")
            onComplete()
            return
        }
        runCatching {
            val mp = MediaPlayer()
            mp.setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build(),
            )
            mp.setDataSource(file.absolutePath)
            mp.setOnPreparedListener { player ->
                // 若在 prepare 完成前已 stop()/换曲，勿 start 已废弃实例
                if (mediaPlayerRef.get() !== player) {
                    releaseMediaPlayer(player)
                    return@setOnPreparedListener
                }
                runCatching {
                    player.start()
                    Log.d(TAG, "playback started ok path=$path")
                }.onFailure { e ->
                    Log.e(TAG, "start failed", e)
                    mediaPlayerRef.compareAndSet(player, null)
                    releaseMediaPlayer(player)
                    onComplete()
                }
            }
            mp.setOnCompletionListener { player ->
                mediaPlayerRef.compareAndSet(player, null)
                releaseMediaPlayer(player)
                onComplete()
            }
            mp.setOnErrorListener { player, what, extra ->
                Log.e(TAG, "MediaPlayer error what=$what extra=$extra path=$path")
                mediaPlayerRef.compareAndSet(player, null)
                releaseMediaPlayer(player)
                onComplete()
                true
            }
            mediaPlayerRef.set(mp)
            mp.prepareAsync()
        }.onFailure { e ->
            Log.e(TAG, "playFile failed path=$path", e)
            mediaPlayerRef.set(null)
            onComplete()
        }
    }

    fun stop() {
        val mp = mediaPlayerRef.getAndSet(null) ?: return
        releaseMediaPlayer(mp)
    }
}
