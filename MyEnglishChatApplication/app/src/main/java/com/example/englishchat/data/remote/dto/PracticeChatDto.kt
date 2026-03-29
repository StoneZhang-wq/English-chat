package com.example.englishchat.data.remote.dto

import com.google.gson.annotations.SerializedName

data class ChatMessageDto(
    val role: String,
    val content: String,
)

data class PracticeChatRequest(
    val messages: List<ChatMessageDto>,
    @SerializedName("scenario_title") val scenarioTitle: String? = null,
)

data class PracticeChatResponse(
    val reply: String,
)
