package com.example.my_english_chat

import android.os.Bundle
import android.util.Log
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // flutter_kitten_tts 在 Dart 侧通过 FFI 打开 libespeak-ng.so；部分机型/构建下需先装入进程，
        // 否则会出现 dlopen failed: library "libespeak-ng.so" not found。
        try {
            System.loadLibrary("espeak-ng")
        } catch (e: UnsatisfiedLinkError) {
            Log.w(
                TAG,
                "Preload libespeak-ng failed; Kitten TTS will fall back to system TTS if needed: ${e.message}",
            )
        }
        super.onCreate(savedInstanceState)
    }

    private companion object {
        private const val TAG = "MainActivity"
    }
}
