package com.example.englishchat.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.automirrored.filled.Chat
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.outlined.Headphones
import androidx.compose.material.icons.automirrored.filled.VolumeDown
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.englishchat.media.PracticeAudioPlayback
import com.example.englishchat.media.PracticeTextToSpeech
import com.example.englishchat.ui.components.EchoTopBar
import com.example.englishchat.asr.VoskModelManager
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import com.example.englishchat.ui.theme.EchoBorder
import com.example.englishchat.ui.theme.EchoDialogueGreen
import com.example.englishchat.ui.theme.EchoMuted
import com.example.englishchat.ui.theme.EchoOnBackground
import com.example.englishchat.ui.theme.EchoSurface
import com.example.englishchat.ui.theme.EchoTaskYellow
import com.example.englishchat.ui.theme.EchoTaskYellowBorder

/**
 * 进入某一场景后的详情：子标签 Shadowing（跟读）与 Practice（练习），
 * Practice：标题右侧为「生成复习资料」入口（不占底部悬浮层，避免挡操作）。
 */
@Composable
fun ScenarioSessionScreen(
    scenarioTitle: String,
    moduleNumber: Int = 1,
    onBack: () -> Unit,
    onGenerateReview: () -> Unit = {},
) {
    var innerTab by remember { mutableIntStateOf(0) } // 0 Shadowing, 1 Practice

    val context = LocalContext.current
    val sharedTts = remember { PracticeTextToSpeech(context.applicationContext) }
    var ttsReady by remember { mutableStateOf(false) }
    DisposableEffect(sharedTts) {
        sharedTts.initialize { ttsReady = it }
        onDispose {
            sharedTts.shutdown()
        }
    }

    /** 进入场景后后台准备 Vosk 模型，避免首次发语音时才长时间下载 */
    LaunchedEffect(Unit) {
        runCatching { VoskModelManager.ensureModel(context.applicationContext) }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        EchoTopBar()
        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 20.dp)
                .padding(bottom = 8.dp),
        ) {
            Text(
                text = "< BACK TO SCENARIOS",
                style = MaterialTheme.typography.labelMedium,
                color = EchoMuted,
                modifier = Modifier
                    .padding(top = 8.dp)
                    .clickable(onClick = onBack),
            )
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    text = scenarioTitle,
                    style = MaterialTheme.typography.headlineMedium,
                    color = EchoOnBackground,
                    modifier = Modifier.weight(1f),
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                if (innerTab == 1) {
                    IconButton(
                        onClick = onGenerateReview,
                    ) {
                        Icon(
                            Icons.Filled.Description,
                            contentDescription = "生成复习资料",
                            tint = Color(0xFF9CA3AF),
                        )
                    }
                }
            }
            val modeLabel = if (innerTab == 0) "SHADOWING" else "PRACTICE"
            Text(
                text = "MODULE %02d / %s".format(moduleNumber, modeLabel),
                style = MaterialTheme.typography.labelSmall,
                color = EchoMuted,
                modifier = Modifier.padding(top = 6.dp, bottom = 16.dp),
            )

            InnerModeTabs(
                selectedIndex = innerTab,
                onSelect = { innerTab = it },
            )

            Spacer(modifier = Modifier.height(16.dp))

            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
            ) {
                when (innerTab) {
                    0 -> Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .verticalScroll(rememberScrollState()),
                    ) {
                        ShadowingModePanel(
                            sharedTts = sharedTts,
                            ttsReady = ttsReady,
                        )
                    }
                    else -> PracticeModePanel(
                        scenarioTitle = scenarioTitle,
                        sharedTts = sharedTts,
                        ttsReady = ttsReady,
                        modifier = Modifier.fillMaxSize(),
                    )
                }
            }
        }
    }
}

@Composable
private fun InnerModeTabs(
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
) {
    // 全宽平分，避免窄屏上 Arrangement.End 把「PRACTICE」挤出屏幕外
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, EchoBorder, RoundedCornerShape(12.dp))
            .background(EchoSurface),
    ) {
        InnerTabItem(
            label = "1. SHADOWING",
            icon = Icons.Outlined.Headphones,
            selected = selectedIndex == 0,
            onClick = { onSelect(0) },
            modifier = Modifier.weight(1f),
        )
        InnerTabItem(
            label = "2. PRACTICE",
            icon = Icons.AutoMirrored.Filled.Chat,
            selected = selectedIndex == 1,
            onClick = { onSelect(1) },
            modifier = Modifier.weight(1f),
        )
    }
}

@Composable
private fun InnerTabItem(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
            .clickable(onClick = onClick)
            .padding(vertical = 12.dp, horizontal = 8.dp),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(18.dp),
                tint = if (selected) EchoOnBackground else EchoMuted,
            )
            Spacer(modifier = Modifier.size(6.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                color = if (selected) EchoOnBackground else EchoMuted,
                maxLines = 2,
                textAlign = TextAlign.Center,
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
        Box(
            modifier = Modifier
                .height(2.dp)
                .fillMaxWidth()
                .background(if (selected) EchoOnBackground else Color.Transparent),
        )
    }
}

@Composable
private fun ShadowingModePanel(
    sharedTts: PracticeTextToSpeech,
    ttsReady: Boolean,
) {
    val scope = rememberCoroutineScope()
    val dialogueLines = remember {
        listOf(
            "Hello, I have a reservation under the name Smith for three nights.",
            "Good evening, Mr. Smith. May I see your ID and credit card for incidentals?",
        )
    }
    val dialogueForTts = remember(dialogueLines) { dialogueLines.joinToString(" ") }
    var shadowingPlaying by remember { mutableStateOf(false) }
    var playbackEndJob by remember { mutableStateOf<Job?>(null) }

    fun togglePlayOriginal() {
        playbackEndJob?.cancel()
        playbackEndJob = null
        if (shadowingPlaying) {
            sharedTts.stop()
            shadowingPlaying = false
            return
        }
        if (!ttsReady || dialogueForTts.isBlank()) return
        PracticeAudioPlayback.stop()
        sharedTts.stop()
        sharedTts.speakQueued(dialogueLines, "shadowing")
        shadowingPlaying = true
        val estimateMs = (dialogueForTts.length * 80L).coerceIn(1200L, 45000L)
        playbackEndJob = scope.launch {
            delay(estimateMs)
            shadowingPlaying = false
        }
    }

    Column(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .border(1.dp, EchoBorder, RoundedCornerShape(16.dp))
                .background(EchoSurface)
                .padding(20.dp),
        ) {
            DialogueLine("SPEAKER A", dialogueLines[0])
            Spacer(modifier = Modifier.height(16.dp))
            DialogueLine("SPEAKER B", dialogueLines[1])
            Spacer(modifier = Modifier.height(20.dp))
            WaveformPlaceholder()
        }

        Spacer(modifier = Modifier.height(28.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedButtonSmall(
                label = "0.75X SPEED",
                icon = Icons.AutoMirrored.Filled.VolumeDown,
                onClick = { },
            )
            Box(
                modifier = Modifier
                    .size(72.dp)
                    .clip(CircleShape)
                    .background(EchoOnBackground),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    Icons.Filled.Mic,
                    contentDescription = "录音",
                    tint = Color.White,
                    modifier = Modifier.size(32.dp),
                )
            }
            OutlinedButtonSmall(
                label = if (shadowingPlaying) "STOP" else "PLAY ORIGINAL",
                icon = Icons.Filled.PlayArrow,
                onClick = { togglePlayOriginal() },
            )
        }
    }
}

@Composable
private fun DialogueLine(speaker: String, line: String) {
    Column {
        Text(
            text = speaker,
            style = MaterialTheme.typography.labelSmall,
            color = EchoMuted,
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = line,
            style = MaterialTheme.typography.bodyLarge.copy(
                fontStyle = FontStyle.Italic,
                color = EchoDialogueGreen,
            ),
        )
    }
}

@Composable
private fun WaveformPlaceholder() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(48.dp)
            .clip(RoundedCornerShape(8.dp))
            .background(Color(0xFFF0F0F0)),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = "～～～",
            style = MaterialTheme.typography.bodyMedium,
            color = EchoMuted,
        )
    }
}

@Composable
private fun OutlinedButtonSmall(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    onClick: () -> Unit,
) {
    OutlinedButton(
        onClick = onClick,
        shape = RoundedCornerShape(12.dp),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 10.dp, vertical = 6.dp),
    ) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(16.dp))
        Spacer(modifier = Modifier.size(4.dp))
        Text(label, style = MaterialTheme.typography.labelSmall, maxLines = 2)
    }
}
