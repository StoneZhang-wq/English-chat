package com.example.englishchat.asr

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.concurrent.TimeUnit
import java.util.zip.ZipInputStream

/**
 * 首次使用时从官方镜像下载并解压 [vosk-model-small-en-us-0.15](https://alphacephei.com/vosk/models)（约 40MB）。
 */
object VoskModelManager {

    /** 避免场景页预取与发送语音同时触发两次下载 */
    private val ensureMutex = Mutex()

    const val MODEL_DIR_NAME = "vosk-model-small-en-us-0.15"

    private const val MODEL_ZIP_URL =
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

    private val httpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(120, TimeUnit.SECONDS)
            .readTimeout(300, TimeUnit.SECONDS)
            .build()
    }

    fun modelDirectory(context: Context): File =
        File(context.filesDir, MODEL_DIR_NAME)

    fun isModelReady(context: Context): Boolean {
        val am = File(modelDirectory(context), "am/final.mdl")
        return am.exists() && am.length() > 0L
    }

    /**
     * 若模型未就绪则下载并解压（可并发调用，内部单飞）。
     */
    suspend fun ensureModel(context: Context) {
        if (isModelReady(context)) return
        ensureMutex.withLock {
            if (isModelReady(context)) return@withLock
            withContext(Dispatchers.IO) {
                val zipFile = File(context.cacheDir, "$MODEL_DIR_NAME.zip")
                downloadToFile(zipFile)
                unzipToFilesDir(zipFile, context.filesDir)
                zipFile.delete()
                if (!isModelReady(context)) {
                    error("解压后未找到模型文件，请检查存储空间后重试")
                }
            }
        }
    }

    private fun downloadToFile(dest: File) {
        val request = Request.Builder().url(MODEL_ZIP_URL).build()
        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                error("下载语音模型失败: HTTP ${response.code}")
            }
            val body = response.body ?: error("下载语音模型失败: 空响应")
            body.byteStream().use { input ->
                FileOutputStream(dest).use { output -> input.copyTo(output) }
            }
        }
    }

    private fun unzipToFilesDir(zipFile: File, filesDir: File) {
        val base = filesDir.canonicalPath + File.separator
        ZipInputStream(FileInputStream(zipFile)).use { zis ->
            var entry = zis.nextEntry
            while (entry != null) {
                val outFile = File(filesDir, entry.name)
                val canonical = outFile.canonicalPath
                if (!canonical.startsWith(base)) {
                    error("非法压缩包路径")
                }
                if (entry.isDirectory) {
                    outFile.mkdirs()
                } else {
                    outFile.parentFile?.mkdirs()
                    FileOutputStream(outFile).use { out -> zis.copyTo(out) }
                }
                zis.closeEntry()
                entry = zis.nextEntry
            }
        }
    }
}
