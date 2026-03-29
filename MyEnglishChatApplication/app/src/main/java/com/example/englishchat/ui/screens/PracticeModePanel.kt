package com.example.englishchat.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import android.media.MediaMetadataRetriever
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.core.content.ContextCompat
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.ThumbUp
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material.icons.outlined.ExpandLess
import androidx.compose.material.icons.outlined.ExpandMore
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.VerticalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChange
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import com.example.englishchat.data.practice.PracticeMessage
import com.example.englishchat.data.practice.VoiceBubbleUiState
import com.example.englishchat.data.remote.dto.ChatMessageDto
import com.example.englishchat.asr.VoskEnglishTranscriber
import com.example.englishchat.asr.VoskModelManager
import com.example.englishchat.data.repository.PracticeChatRepository
import com.example.englishchat.media.PracticeAudioPlayback
import com.example.englishchat.media.PracticeAudioRecorder
import com.example.englishchat.media.practiceRecordedWavDurationMs
import com.example.englishchat.media.practiceRecordedWavDurationMsFromOurFile
import com.example.englishchat.media.PracticeTextToSpeech
import com.example.englishchat.ui.theme.EchoBorder
import com.example.englishchat.ui.theme.EchoMuted
import com.example.englishchat.ui.theme.EchoOnBackground
import com.example.englishchat.ui.theme.EchoSurface
import com.example.englishchat.ui.theme.EchoTaskYellow
import com.example.englishchat.ui.theme.EchoTaskYellowBorder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow

/** 长按低于此毫秒视为「短点」，不录音（与微信类似，约 0.3s） */
private const val MIC_LONG_PRESS_MS = 300L

/** 练习页输入区主色（麦克风 / 发送 / 录音条） */
private val PracticeChatGreen = Color(0xFF4CAF50)

private const val DEMO_USER_TRANSLATION =
    "（演示译文）This is a placeholder English translation."
private const val DEMO_AI_TRANSLATION = "（演示译文）这是 AI 回复的占位中文翻译。"
private const val DEMO_OPTIMIZED =
    "（演示优化）Here's a more natural phrasing you could use in conversation."

@Composable
fun PracticeModePanel(
    scenarioTitle: String,
    sharedTts: PracticeTextToSpeech,
    ttsReady: Boolean,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    var messages by remember { mutableStateOf<List<PracticeMessage>>(emptyList()) }
    var inputValue by remember { mutableStateOf(TextFieldValue("")) }
    var sending by remember { mutableStateOf(false) }
    /** 离线 ASR：下载模型 / Vosk 转写 */
    var transcribing by remember { mutableStateOf(false) }
    /** 模型尚未就绪时在练习页后台拉取（与场景页预取共享单飞，不阻塞打字） */
    var modelPreparing by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val voiceUi = remember { mutableStateMapOf<Long, VoiceBubbleUiState>() }
    var playingId by remember { mutableLongStateOf(-1L) }
    var recording by remember { mutableStateOf(false) }
    /** MediaRecorder 是否已真正 start（无权限时仅有录音 UI，未 start） */
    var recorderActive by remember { mutableStateOf(false) }
    var recordCancelHint by remember { mutableStateOf(false) }
    var micHint by remember { mutableStateOf<String?>(null) }

    val recorder = remember { PracticeAudioRecorder(context) }
    val repo = remember { PracticeChatRepository() }
    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()

    DisposableEffect(sharedTts) {
        onDispose {
            PracticeAudioPlayback.stop()
            sharedTts.stop()
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (!granted) {
            error = "需要麦克风权限才能使用语音输入"
        } else if (recording && !recorderActive) {
            try {
                recorder.start()
                recorderActive = true
                error = null
            } catch (e: Exception) {
                recording = false
                error = "无法开始录音：${e.message ?: "未知错误"}"
            }
        }
    }

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.scrollToItem(messages.lastIndex)
        }
    }

    LaunchedEffect(micHint) {
        if (micHint != null) {
            delay(4000)
            micHint = null
        }
    }

    LaunchedEffect(Unit) {
        val app = context.applicationContext
        if (VoskModelManager.isModelReady(app)) return@LaunchedEffect
        modelPreparing = true
        try {
            VoskModelManager.ensureModel(app)
        } finally {
            modelPreparing = false
        }
    }

    var recordingElapsedSec by remember { mutableStateOf(0) }
    LaunchedEffect(recording) {
        if (!recording) {
            recordingElapsedSec = 0
            return@LaunchedEffect
        }
        recordingElapsedSec = 0
        while (true) {
            delay(1000)
            recordingElapsedSec++
        }
    }

    val onPlayVoice: (PracticeMessage.Voice) -> Unit = { msg ->
        val id = msg.id
        if (playingId == id) {
            PracticeAudioPlayback.stop()
            sharedTts.stop()
            playingId = -1L
        } else {
            PracticeAudioPlayback.stop()
            sharedTts.stop()
            playingId = id
            if (msg.isAiTts || msg.audioPath.isBlank()) {
                if (ttsReady) {
                    sharedTts.speak(msg.transcript, "ai_${msg.id}")
                }
                scope.launch {
                    delay((msg.transcript.length * 80L).coerceIn(800L, 20000L))
                    if (playingId == id) playingId = -1L
                }
            } else {
                PracticeAudioPlayback.playFile(msg.audioPath) {
                    if (playingId == id) playingId = -1L
                }
            }
        }
    }

    Column(modifier = modifier.fillMaxSize()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, EchoTaskYellowBorder, RoundedCornerShape(12.dp))
                .background(EchoTaskYellow)
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "CURRENT TASK:",
                style = MaterialTheme.typography.labelSmall,
                color = EchoMuted,
                modifier = Modifier.padding(end = 8.dp),
            )
            Text(
                text = scenarioTitle.ifBlank { "Practice in this scenario." },
                style = MaterialTheme.typography.bodyMedium,
                color = EchoOnBackground,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .heightIn(min = 120.dp)
                .clip(RoundedCornerShape(16.dp))
                .border(1.dp, EchoBorder, RoundedCornerShape(16.dp))
                .background(EchoSurface),
        ) {
            if (messages.isEmpty() && !sending) {
                Text(
                    text = "输入文字后点键盘「发送」；或长按右侧黑色麦克风说话，松手发送、上滑取消。",
                    style = MaterialTheme.typography.bodySmall,
                    color = EchoMuted,
                    modifier = Modifier.padding(16.dp),
                )
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    items(messages, key = { it.id }) { msg ->
                        when (msg) {
                            is PracticeMessage.Text -> PracticeTextBubble(msg)
                            is PracticeMessage.Voice -> {
                                val st = voiceUi[msg.id] ?: VoiceBubbleUiState()
                                PracticeVoiceBubble(
                                    msg = msg,
                                    state = st,
                                    isPlaying = playingId == msg.id,
                                    onPlay = { onPlayVoice(msg) },
                                    onToggleExpand = {
                                        val cur = voiceUi[msg.id] ?: VoiceBubbleUiState()
                                        voiceUi[msg.id] = cur.copy(expanded = !cur.expanded)
                                    },
                                    onToggleTranslate = {
                                        val cur = voiceUi[msg.id] ?: VoiceBubbleUiState()
                                        val show = !cur.translationVisible
                                        val t =
                                            if (msg.isUser) DEMO_USER_TRANSLATION else DEMO_AI_TRANSLATION
                                        voiceUi[msg.id] = cur.copy(
                                            translationVisible = show,
                                            translatedText = if (show) (cur.translatedText ?: t) else cur.translatedText,
                                        )
                                    },
                                    onToggleOptimize = {
                                        val cur = voiceUi[msg.id] ?: VoiceBubbleUiState()
                                        val show = !cur.optimizedSectionVisible
                                        voiceUi[msg.id] = cur.copy(
                                            optimizedSectionVisible = show,
                                            optimizedText =
                                                if (show) (cur.optimizedText ?: DEMO_OPTIMIZED) else cur.optimizedText,
                                        )
                                    },
                                )
                            }
                        }
                    }
                }
            }
            if (sending && messages.isNotEmpty()) {
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(8.dp),
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(28.dp),
                        strokeWidth = 3.dp,
                    )
                }
            }
        }

        error?.let { err ->
            Text(
                text = err,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.padding(top = 8.dp),
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        val density = LocalDensity.current
        val cancelPx = remember(density) { with(density) { 72.dp.toPx() } }

        val sendTextMessage: () -> Unit = sendText@{
            val text = inputValue.text.trim()
            if (text.isEmpty() || sending || transcribing) return@sendText
            error = null
            val userMsg = PracticeMessage.Text(
                id = System.nanoTime(),
                isUser = true,
                body = text,
            )
            val afterUser = messages + userMsg
            messages = afterUser
            inputValue = TextFieldValue("")
            sendAssistantReply(
                afterUser,
                scenarioTitle,
                repo,
                scope,
                onSending = { sending = it },
                onError = { error = it },
                onAssistant = { assistantMsg -> messages = afterUser + assistantMsg },
            )
        }

        PracticeUnifiedInputBar(
            inputValue = inputValue,
            onInputChange = { inputValue = it },
            sending = sending,
            modelPreparing = modelPreparing,
            transcribing = transcribing,
            recording = recording,
            recordingElapsedSec = recordingElapsedSec,
            recordCancelHint = recordCancelHint,
            cancelThresholdPx = cancelPx,
            onSendText = sendTextMessage,
            onPromptBulbClick = {
                micHint = "提示内容生成将在后续版本开放"
            },
            onRecordStart = {
                error = null
                recordCancelHint = false
                recording = true
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) !=
                    PackageManager.PERMISSION_GRANTED
                ) {
                    permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                } else {
                    try {
                        recorder.start()
                        recorderActive = true
                    } catch (e: Exception) {
                        recording = false
                        recorderActive = false
                        error = "无法开始录音：${e.message ?: "未知错误"}"
                    }
                }
            },
            onMicShortTap = {
                micHint = "长按麦克风说话，松手发送语音；上滑取消。"
            },
            onRecordCancel = {
                recording = false
                recordCancelHint = false
                if (recorderActive) {
                    recorderActive = false
                    recorder.cancel()
                }
            },
            onRecordSend = {
                recording = false
                recordCancelHint = false
                if (!recorderActive) {
                    if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) !=
                        PackageManager.PERMISSION_GRANTED
                    ) {
                        error = "需要麦克风权限才能发送语音"
                    }
                } else {
                    // 先停采集再排队 IO，否则协程晚几 ms～若干秒执行 stop() 时会多录一长段静音
                    recorder.signalStopCapture()
                    recorderActive = false
                    // stop() 内含 thread.join + 写 WAV，不得在 UI 线程执行，否则会触发「应用无响应」
                    scope.launch {
                        val file = withContext(Dispatchers.IO) {
                            recorder.stop()
                        }
                        if (file == null) {
                            error = "录音过短或失败"
                            return@launch
                        }
                        val path = file.absolutePath
                        val durationMs = practiceRecordedWavDurationMsFromOurFile(file)
                            ?: practiceRecordedWavDurationMs(path)
                            ?: audioDurationMs(path)
                        // 与 English-Chat 一致：停录后立刻上屏占位，转写在后台完成后再更新文案并请求 AI
                        val msgId = System.nanoTime()
                        val placeholderVoice = PracticeMessage.Voice(
                            id = msgId,
                            isUser = true,
                            audioPath = path,
                            durationMs = durationMs,
                            transcript = "转写中…",
                            isAiTts = false,
                        )
                        messages = messages + placeholderVoice
                        voiceUi[msgId] = VoiceBubbleUiState()

                        transcribing = true
                        error = null
                        val transcript = try {
                            withContext(Dispatchers.IO) {
                                VoskModelManager.ensureModel(context.applicationContext)
                                VoskEnglishTranscriber.transcribe(
                                    context.applicationContext,
                                    path,
                                )
                            }.ifBlank {
                                "（未识别到内容：请说英文、靠近麦克风；中文需换模型；可看 Logcat 标签 VoskEnglishTranscriber）"
                            }
                        } catch (e: Exception) {
                            error = "语音模型或识别失败：${e.message ?: "未知错误"}（首次使用需联网下载约 40MB 模型）"
                            "（识别失败）"
                        } finally {
                            transcribing = false
                        }
                        messages = messages.map { m ->
                            if (m is PracticeMessage.Voice && m.id == msgId) {
                                m.copy(transcript = transcript)
                            } else {
                                m
                            }
                        }
                        val afterUser = messages
                        sendAssistantReply(
                            afterUser,
                            scenarioTitle,
                            repo,
                            scope,
                            onSending = { sending = it },
                            onError = { error = it },
                            onAssistant = { assistantMsg ->
                                messages = afterUser + assistantMsg
                                if (assistantMsg is PracticeMessage.Voice) {
                                    voiceUi[assistantMsg.id] = VoiceBubbleUiState()
                                }
                            },
                        )
                    }
                }
            },
            onCancelVisual = { show -> recordCancelHint = show },
        )

        micHint?.let { hint ->
            Text(
                text = hint,
                style = MaterialTheme.typography.labelSmall,
                color = EchoMuted,
                modifier = Modifier.padding(top = 6.dp),
            )
        }
    }
}

@Composable
private fun PracticeUnifiedInputBar(
    inputValue: TextFieldValue,
    onInputChange: (TextFieldValue) -> Unit,
    sending: Boolean,
    modelPreparing: Boolean,
    transcribing: Boolean,
    recording: Boolean,
    recordingElapsedSec: Int,
    recordCancelHint: Boolean,
    cancelThresholdPx: Float,
    onSendText: () -> Unit,
    onRecordStart: () -> Unit,
    onRecordCancel: () -> Unit,
    onRecordSend: () -> Unit,
    onCancelVisual: (Boolean) -> Unit,
    onMicShortTap: () -> Unit,
    onPromptBulbClick: () -> Unit,
) {
    val onStart by rememberUpdatedState(onRecordStart)
    val onCancel by rememberUpdatedState(onRecordCancel)
    val onSend by rememberUpdatedState(onRecordSend)
    val onVisual by rememberUpdatedState(onCancelVisual)
    val onSendTextState by rememberUpdatedState(onSendText)
    val onShortTap by rememberUpdatedState(onMicShortTap)
    val onBulb by rememberUpdatedState(onPromptBulbClick)

    val micBgColor = when {
        recording && recordCancelHint -> Color(0xFFB71C1C)
        recording -> Color(0xFFE53935)
        else -> PracticeChatGreen
    }
    val micRingColor = if (recording) Color.White.copy(alpha = 0.45f) else Color.Transparent

    val inputBusy = sending || transcribing
    val canSendText = inputValue.text.isNotBlank() && !inputBusy && !recording

    Column(modifier = Modifier.fillMaxWidth()) {
        when {
            transcribing && !recording -> Text(
                text = "正在识别语音…",
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.bodySmall,
                color = EchoMuted,
            )
            modelPreparing && !recording -> Text(
                text = "正在准备离线语音模型（约 40MB，首次需联网），可先打字；就绪后再发语音更顺畅。",
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.bodySmall,
                color = EchoMuted,
            )
        }
        if (recording) {
            Text(
                text = if (recordCancelHint) "松开手指，取消发送" else "松开发送，上滑取消",
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.bodySmall,
                color = if (recordCancelHint) MaterialTheme.colorScheme.error else EchoOnBackground.copy(alpha = 0.65f),
            )
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(20.dp))
                    .border(1.dp, PracticeChatGreen.copy(alpha = 0.45f), RoundedCornerShape(20.dp))
                    .background(Color.White)
                    .clickable(onClick = onBulb)
                    .padding(horizontal = 10.dp, vertical = 8.dp),
            ) {
                Icon(
                    Icons.Filled.Lightbulb,
                    contentDescription = "生成提示",
                    tint = PracticeChatGreen,
                    modifier = Modifier.size(22.dp),
                )
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            // 左侧麦克风：手势层与背景分层，避免 recording 时重建导致长按中断
            Box(
                modifier = Modifier.size(48.dp),
                contentAlignment = Alignment.Center,
            ) {
                Box(
                    Modifier
                        .fillMaxSize()
                        .clip(RoundedCornerShape(24.dp))
                        .border(2.dp, micRingColor, RoundedCornerShape(24.dp))
                        .background(micBgColor),
                )
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .then(
                            if (!inputBusy) {
                                Modifier.pointerInput(cancelThresholdPx) {
                                    awaitEachGesture {
                                        val down = awaitFirstDown(requireUnconsumed = false)
                                        val pointerId = down.id
                                        val releasedWithinThreshold = withTimeoutOrNull(MIC_LONG_PRESS_MS) {
                                            waitForUpOrCancellation()
                                        }
                                        if (releasedWithinThreshold != null) {
                                            onShortTap()
                                            return@awaitEachGesture
                                        }
                                        onStart()
                                        var totalY = 0f
                                        while (true) {
                                            val event = awaitPointerEvent(PointerEventPass.Main)
                                            val change = event.changes.firstOrNull { it.id == pointerId }
                                                ?: continue
                                            totalY += change.positionChange().y
                                            onVisual(totalY < -cancelThresholdPx)
                                            if (change.changedToUp()) break
                                        }
                                        onVisual(false)
                                        if (totalY < -cancelThresholdPx) onCancel() else onSend()
                                    }
                                }
                            } else {
                                Modifier
                            },
                        ),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Filled.Mic,
                        contentDescription = "按住说话",
                        tint = Color.White,
                        modifier = Modifier.size(24.dp),
                    )
                }
            }
            if (recording) {
                val barColor = if (recordCancelHint) Color(0xFFC62828) else PracticeChatGreen
                Row(
                    modifier = Modifier
                        .weight(1f)
                        .heightIn(min = 48.dp)
                        .clip(RoundedCornerShape(24.dp))
                        .background(barColor)
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    WaveformMini(barColor = Color.White.copy(alpha = 0.9f))
                    Text(
                        text = "${recordingElapsedSec.coerceAtLeast(0)}s",
                        style = MaterialTheme.typography.labelLarge,
                        color = Color.White,
                    )
                }
            } else {
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .heightIn(min = 48.dp)
                        .clip(RoundedCornerShape(24.dp))
                        .background(Color.White)
                        .border(1.dp, EchoBorder.copy(alpha = 0.35f), RoundedCornerShape(24.dp)),
                ) {
                    TextField(
                        value = inputValue,
                        onValueChange = onInputChange,
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !inputBusy,
                        placeholder = {
                            Text(
                                "对话",
                                style = MaterialTheme.typography.bodyMedium,
                                color = EchoMuted,
                            )
                        },
                        colors = TextFieldDefaults.colors(
                            focusedContainerColor = Color.Transparent,
                            unfocusedContainerColor = Color.Transparent,
                            disabledContainerColor = Color.Transparent,
                            focusedIndicatorColor = Color.Transparent,
                            unfocusedIndicatorColor = Color.Transparent,
                            disabledIndicatorColor = Color.Transparent,
                            cursorColor = EchoOnBackground,
                            focusedTextColor = EchoOnBackground,
                            unfocusedTextColor = EchoOnBackground,
                        ),
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                        keyboardActions = KeyboardActions(
                            onSend = { onSendTextState() },
                        ),
                        minLines = 1,
                        maxLines = 4,
                    )
                }
            }
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .background(
                        if (canSendText) PracticeChatGreen else EchoMuted.copy(alpha = 0.35f),
                    )
                    .clickable(
                        enabled = canSendText,
                        onClick = { onSendTextState() },
                    ),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.Send,
                    contentDescription = "发送",
                    tint = Color.White,
                    modifier = Modifier.size(24.dp),
                )
            }
        }
        Text(
            text = "内容由 AI 生成",
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 10.dp),
            textAlign = TextAlign.Center,
            style = MaterialTheme.typography.labelSmall,
            color = EchoMuted,
        )
    }
}

@Composable
private fun PracticeTextBubble(msg: PracticeMessage.Text) {
    val align = if (msg.isUser) Alignment.End else Alignment.Start
    val bg = if (msg.isUser) EchoOnBackground.copy(alpha = 0.12f) else Color(0xFFF0F4F8)
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = align,
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(bg)
                .padding(horizontal = 12.dp, vertical = 8.dp),
        ) {
            Text(
                text = msg.body,
                style = MaterialTheme.typography.bodyMedium,
                color = EchoOnBackground,
            )
        }
    }
}

private val PracticeVoiceUserCardBg = Color(0xFFE8F5E9)
private val PracticeVoiceAiCardBg = Color(0xFFF0F4F8)
private val PracticeAnalysisGreen = Color(0xFF4CAF50)
private val PracticeAnalysisYellow = Color(0xFFFFC107)
private val PracticeAnalysisOrange = Color(0xFFFF9800)

/** 发音分占位，后续接评测接口 */
private const val PRONUNCIATION_SCORE_PLACEHOLDER = 100

@Composable
private fun PracticeVoiceBubble(
    msg: PracticeMessage.Voice,
    state: VoiceBubbleUiState,
    isPlaying: Boolean,
    onPlay: () -> Unit,
    onToggleExpand: () -> Unit,
    onToggleTranslate: () -> Unit,
    onToggleOptimize: () -> Unit,
) {
    val align = if (msg.isUser) Alignment.End else Alignment.Start
    val barBg = if (msg.isUser) EchoOnBackground.copy(alpha = 0.12f) else Color(0xFFF0F4F8)
    val cardBg = if (msg.isUser) PracticeVoiceUserCardBg else PracticeVoiceAiCardBg

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = align,
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            IconButton(onClick = onPlay, modifier = Modifier.size(40.dp)) {
                Icon(
                    Icons.Filled.PlayArrow,
                    contentDescription = "播放",
                    tint = if (isPlaying) EchoOnBackground else EchoMuted,
                    modifier = Modifier.size(22.dp),
                )
            }
            Row(
                modifier = Modifier
                    .widthIn(max = 240.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(barBg)
                    .clickable(onClick = onToggleExpand)
                    .padding(horizontal = 10.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                WaveformMini()
                Text(
                    text = formatDuration(msg.durationMs),
                    style = MaterialTheme.typography.labelMedium,
                    color = EchoMuted,
                )
            }
        }
        if (!state.expanded) {
            Text(
                text = "点击语音条查看英文",
                style = MaterialTheme.typography.labelSmall,
                color = EchoMuted,
                modifier = Modifier.padding(top = 4.dp, start = 4.dp, end = 4.dp),
            )
        } else {
            Spacer(modifier = Modifier.height(6.dp))
            Column(
                modifier = Modifier
                    .widthIn(max = 300.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .border(1.dp, EchoBorder.copy(alpha = 0.35f), RoundedCornerShape(14.dp))
                    .background(cardBg)
                    .padding(horizontal = 12.dp, vertical = 10.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = msg.transcript,
                        style = MaterialTheme.typography.bodyMedium,
                        color = EchoOnBackground,
                        modifier = Modifier.weight(1f),
                    )
                    IconButton(
                        onClick = onPlay,
                        modifier = Modifier.size(36.dp),
                    ) {
                        Icon(
                            Icons.Filled.PlayArrow,
                            contentDescription = "播放",
                            tint = if (isPlaying) PracticeAnalysisGreen else EchoMuted,
                            modifier = Modifier.size(22.dp),
                        )
                    }
                }
                if (msg.isUser) {
                    if (state.translationVisible && state.translatedText != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = state.translatedText,
                            style = MaterialTheme.typography.bodySmall,
                            color = EchoOnBackground,
                        )
                    }
                    HorizontalDivider(
                        modifier = Modifier.padding(vertical = 10.dp),
                        color = EchoBorder.copy(alpha = 0.4f),
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        IconButton(
                            onClick = onToggleTranslate,
                            modifier = Modifier.size(36.dp),
                        ) {
                            Icon(
                                Icons.Filled.Translate,
                                contentDescription = if (state.translationVisible) "隐藏翻译" else "显示翻译",
                                tint = if (state.translationVisible) PracticeAnalysisGreen else EchoMuted,
                                modifier = Modifier.size(22.dp),
                            )
                        }
                        Row(
                            modifier = Modifier
                                .clip(RoundedCornerShape(8.dp))
                                .clickable(onClick = onToggleOptimize)
                                .padding(horizontal = 6.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(2.dp),
                        ) {
                            Text(
                                text = "优化表达",
                                style = MaterialTheme.typography.labelMedium,
                                color = EchoOnBackground,
                            )
                            Icon(
                                imageVector = if (state.optimizedSectionVisible) {
                                    Icons.Outlined.ExpandLess
                                } else {
                                    Icons.Outlined.ExpandMore
                                },
                                contentDescription = null,
                                tint = EchoMuted,
                                modifier = Modifier.size(18.dp),
                            )
                        }
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(2.dp),
                            ) {
                                Text("语法", style = MaterialTheme.typography.labelSmall, color = EchoMuted)
                                Icon(
                                    Icons.Filled.ThumbUp,
                                    contentDescription = null,
                                    tint = PracticeAnalysisGreen,
                                    modifier = Modifier.size(14.dp),
                                )
                            }
                            VerticalDivider(
                                modifier = Modifier.height(16.dp),
                                color = EchoBorder.copy(alpha = 0.5f),
                            )
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(2.dp),
                            ) {
                                Text("用词", style = MaterialTheme.typography.labelSmall, color = EchoMuted)
                                Icon(
                                    Icons.Filled.ThumbUp,
                                    contentDescription = null,
                                    tint = PracticeAnalysisYellow,
                                    modifier = Modifier.size(14.dp),
                                )
                            }
                            VerticalDivider(
                                modifier = Modifier.height(16.dp),
                                color = EchoBorder.copy(alpha = 0.5f),
                            )
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(2.dp),
                            ) {
                                Text("发音", style = MaterialTheme.typography.labelSmall, color = EchoMuted)
                                Text(
                                    text = PRONUNCIATION_SCORE_PLACEHOLDER.toString(),
                                    style = MaterialTheme.typography.labelMedium,
                                    color = PracticeAnalysisOrange,
                                )
                            }
                        }
                    }
                    if (state.optimizedSectionVisible && state.optimizedText != null) {
                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = state.optimizedText,
                            style = MaterialTheme.typography.bodySmall,
                            color = EchoOnBackground,
                        )
                    }
                } else {
                    Spacer(modifier = Modifier.height(8.dp))
                    IconButton(
                        onClick = onToggleTranslate,
                        modifier = Modifier.size(36.dp),
                    ) {
                        Icon(
                            Icons.Filled.Translate,
                            contentDescription = if (state.translationVisible) "隐藏翻译" else "显示翻译",
                            tint = if (state.translationVisible) PracticeAnalysisGreen else EchoMuted,
                            modifier = Modifier.size(22.dp),
                        )
                    }
                    if (state.translationVisible && state.translatedText != null) {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = state.translatedText,
                            style = MaterialTheme.typography.bodySmall,
                            color = EchoOnBackground,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun WaveformMini(
    barColor: Color = EchoMuted.copy(alpha = 0.5f),
) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        val heights = listOf(6, 12, 8, 14, 10, 16, 9, 13, 7, 11).map { it.dp }
        heights.forEach { h ->
            Box(
                modifier = Modifier
                    .width(3.dp)
                    .height(h)
                    .clip(RoundedCornerShape(2.dp))
                    .background(barColor),
            )
        }
    }
}

private fun formatDuration(ms: Long): String {
    val s = ((ms.coerceAtLeast(0)) / 1000).toInt()
    return "%d:%02d".format(s / 60, s % 60)
}

private fun audioDurationMs(path: String): Long {
    return runCatching {
        val r = MediaMetadataRetriever()
        r.setDataSource(path)
        val d = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 800L
        r.release()
        d
    }.getOrDefault(800L)
}

private fun List<PracticeMessage>.toChatDtos(): List<ChatMessageDto> =
    map {
        when (it) {
            is PracticeMessage.Text -> ChatMessageDto(
                role = if (it.isUser) "user" else "assistant",
                content = it.body,
            )
            is PracticeMessage.Voice -> ChatMessageDto(
                role = if (it.isUser) "user" else "assistant",
                content = it.transcript.ifBlank { "[语音消息]" },
            )
        }
    }

private fun sendAssistantReply(
    history: List<PracticeMessage>,
    scenarioTitle: String,
    repo: PracticeChatRepository,
    scope: kotlinx.coroutines.CoroutineScope,
    onSending: (Boolean) -> Unit,
    onError: (String?) -> Unit,
    onAssistant: (PracticeMessage) -> Unit,
) {
    val payload = history.toChatDtos()
    scope.launch {
        onSending(true)
        try {
            val reply = withContext(Dispatchers.IO) {
                repo.sendChat(
                    messages = payload,
                    scenarioTitle = scenarioTitle.takeIf { it.isNotBlank() },
                )
            }
            onError(null)
            onAssistant(
                PracticeMessage.Voice(
                    id = System.nanoTime(),
                    isUser = false,
                    audioPath = "",
                    durationMs = (reply.length * 60L).coerceIn(1500L, 120_000L),
                    transcript = reply,
                    isAiTts = true,
                ),
            )
        } catch (e: Exception) {
            onError(e.message ?: "请求失败")
        } finally {
            onSending(false)
        }
    }
}
