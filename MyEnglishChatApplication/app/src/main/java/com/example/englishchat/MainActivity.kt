package com.example.englishchat

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.example.englishchat.ui.MainScreen
import com.example.englishchat.ui.theme.MyEnglishChatApplicationTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MyEnglishChatApplicationTheme {
                MainScreen()
            }
        }
    }
}
