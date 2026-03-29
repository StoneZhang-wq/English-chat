package com.example.englishchat.data.repository

import com.example.englishchat.data.remote.PracticeChatApi
import com.example.englishchat.data.remote.RetrofitClient
import com.example.englishchat.data.remote.dto.ChatMessageDto
import com.example.englishchat.data.remote.dto.PracticeChatRequest

class PracticeChatRepository(
    private val api: PracticeChatApi = RetrofitClient.practiceChatApi,
) {
    suspend fun sendChat(
        messages: List<ChatMessageDto>,
        scenarioTitle: String?,
    ): String {
        val body = PracticeChatRequest(messages = messages, scenarioTitle = scenarioTitle)
        return api.practiceChat(body).reply
    }
}
