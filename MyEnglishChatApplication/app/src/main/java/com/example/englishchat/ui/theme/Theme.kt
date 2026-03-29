package com.example.englishchat.ui.theme

import android.os.Build
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val DarkColorScheme = darkColorScheme(
    primary = Amber600,
    onPrimary = Stone900,
    primaryContainer = Stone800,
    onPrimaryContainer = Amber500,
    secondary = Stone700,
    onSecondary = Stone100,
    tertiary = PurpleGrey80,
    background = Stone950,
    onBackground = Stone100,
    surface = Stone900,
    onSurface = Stone200,
    surfaceVariant = Stone800,
    onSurfaceVariant = Stone200,
    outline = Stone700,
)

/** EchoEnglish 式浅色主方案（默认） */
private val EchoLightColorScheme = lightColorScheme(
    primary = EchoOnBackground,
    onPrimary = Color.White,
    primaryContainer = EchoNavSelectedCircle,
    onPrimaryContainer = EchoOnBackground,
    secondary = EchoMuted,
    onSecondary = EchoOnBackground,
    background = EchoBackground,
    onBackground = EchoOnBackground,
    surface = EchoSurface,
    onSurface = EchoOnBackground,
    surfaceVariant = Color(0xFFF0F0EF),
    onSurfaceVariant = EchoMuted,
    outline = EchoBorder,
    outlineVariant = EchoBorder,
)

@Composable
fun MyEnglishChatApplicationTheme(
    /** 产品主界面为 Echo 浅色风，默认不因系统深色而切换 */
    darkTheme: Boolean = false,
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit,
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> EchoLightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content,
    )
}
