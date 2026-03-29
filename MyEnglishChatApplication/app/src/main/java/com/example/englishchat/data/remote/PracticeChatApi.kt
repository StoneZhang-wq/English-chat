package com.example.englishchat.data.remote

import com.example.englishchat.data.remote.dto.PracticeChatRequest
import com.example.englishchat.data.remote.dto.PracticeChatResponse
import retrofit2.http.Body
import retrofit2.http.POST

interface PracticeChatApi {
    @POST("api/practice/chat")
    suspend fun practiceChat(@Body body: PracticeChatRequest): PracticeChatResponse
}
