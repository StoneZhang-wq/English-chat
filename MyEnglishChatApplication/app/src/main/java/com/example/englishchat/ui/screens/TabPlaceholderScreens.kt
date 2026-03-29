package com.example.englishchat.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.People
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.example.englishchat.ui.components.EchoTopBar
import com.example.englishchat.ui.theme.EchoBorder
import com.example.englishchat.ui.theme.EchoMuted
import com.example.englishchat.ui.theme.EchoOnBackground
import com.example.englishchat.ui.theme.EchoSurface
import com.example.englishchat.ui.theme.TypographyP2pTitle

private data class ScenarioItem(val title: String, val quote: String)

private val scenarioItems = listOf(
    ScenarioItem(
        "Job Interview",
        "\"Could you tell us a bit about your background and why you're a good fit for this role?\"",
    ),
    ScenarioItem(
        "Business Meeting",
        "\"Good morning everyone. Today I'd like to present the latest updates on our project.\"",
    ),
    ScenarioItem(
        "Doctor Appointment",
        "\"I've been having a persistent cough and a slight fever for the past three days.\"",
    ),
    ScenarioItem(
        "Hotel Check-in",
        "\"Hello, I have a reservation under the name Smith for three nights.\"",
    ),
)

private data class AiCategoryItem(val title: String, val description: String)

private val aiCategories = listOf(
    AiCategoryItem("Travel & Exploration", "Master the language of the world"),
    AiCategoryItem("Professional Life", "Excel in your career conversations"),
    AiCategoryItem("Daily Life & Culture", "Navigate real situations with confidence"),
)

@Composable
fun ShadowingScreen(
    onScenarioClick: (scenarioTitle: String) -> Unit = {},
) {
    var query by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        EchoTopBar()
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            modifier = Modifier.weight(1f),
            contentPadding = PaddingValues(start = 20.dp, top = 8.dp, end = 20.dp, bottom = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item(span = { GridItemSpan(maxLineSpan) }) {
                Column {
                    Text(
                        text = "Pick a Scenario",
                        style = MaterialTheme.typography.headlineLarge,
                        color = EchoOnBackground,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 8.dp),
                        textAlign = TextAlign.Center,
                    )
                    Text(
                        text = "RECOMMENDED FOR YOU TODAY",
                        style = MaterialTheme.typography.labelSmall,
                        color = EchoMuted,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 12.dp),
                        textAlign = TextAlign.Center,
                    )
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 20.dp, bottom = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        OutlinedTextField(
                            value = query,
                            onValueChange = { query = it },
                            modifier = Modifier.weight(1f),
                            placeholder = {
                                Text(
                                    "What do you want to practice? (e.g., 'at the dentist')",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = EchoMuted,
                                )
                            },
                            singleLine = true,
                            shape = RoundedCornerShape(28.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = EchoBorder,
                                unfocusedBorderColor = EchoBorder,
                                focusedContainerColor = EchoSurface,
                                unfocusedContainerColor = EchoSurface,
                            ),
                        )
                        Button(
                            onClick = { /* 稍后接推荐逻辑 */ },
                            shape = RoundedCornerShape(28.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = EchoOnBackground,
                                contentColor = Color.White,
                            ),
                            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 14.dp),
                        ) {
                            Icon(
                                Icons.Filled.AutoAwesome,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp),
                            )
                            Spacer(modifier = Modifier.size(6.dp))
                            Text("REQUEST", style = MaterialTheme.typography.labelMedium)
                        }
                    }
                }
            }
            items(scenarioItems) { item ->
                ScenarioCard(
                    item = item,
                    onClick = { onScenarioClick(item.title) },
                )
            }
        }
    }
}

@Composable
private fun ScenarioCard(
    item: ScenarioItem,
    onClick: () -> Unit = {},
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .border(1.dp, EchoBorder, RoundedCornerShape(16.dp))
            .background(EchoSurface)
            .clickable(onClick = onClick)
            .padding(16.dp),
    ) {
        Text(
            text = item.title,
            style = MaterialTheme.typography.titleLarge,
            color = EchoOnBackground,
        )
        Spacer(modifier = Modifier.height(10.dp))
        Text(
            text = item.quote,
            style = MaterialTheme.typography.bodyMedium,
            color = EchoMuted,
        )
    }
}

@Composable
fun AiDialogueScreen() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        EchoTopBar()
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 8.dp, bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                Text(
                    text = "AI Dialogue",
                    style = MaterialTheme.typography.headlineLarge,
                    color = EchoOnBackground,
                    modifier = Modifier.fillMaxWidth(),
                    textAlign = TextAlign.Center,
                )
            }
            item {
                Text(
                    text = "SELECT A CATEGORY TO BEGIN YOUR JOURNEY",
                    style = MaterialTheme.typography.labelSmall,
                    color = EchoMuted,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp, bottom = 8.dp),
                    textAlign = TextAlign.Center,
                )
            }
            items(aiCategories) { cat ->
                AiCategoryCard(cat)
            }
        }
    }
}

@Composable
private fun AiCategoryCard(cat: AiCategoryItem) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(168.dp)
            .clip(RoundedCornerShape(20.dp))
            .border(1.dp, EchoBorder, RoundedCornerShape(20.dp)),
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFFE0E0E0)),
        )
        Column(
            modifier = Modifier
                .align(Alignment.CenterStart)
                .padding(horizontal = 22.dp, vertical = 16.dp)
                .fillMaxWidth(0.62f),
        ) {
            Text(
                text = cat.title,
                style = MaterialTheme.typography.titleLarge,
                color = EchoOnBackground,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = cat.description,
                style = MaterialTheme.typography.bodyMedium,
                color = EchoMuted,
            )
        }
    }
}

@Composable
fun P2pScreen() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        EchoTopBar()
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Spacer(modifier = Modifier.height(16.dp))
            Box(
                modifier = Modifier
                    .size(88.dp)
                    .clip(RoundedCornerShape(22.dp))
                    .background(EchoOnBackground),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.Filled.People,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(40.dp),
                )
            }
            Spacer(modifier = Modifier.height(20.dp))
            Text(
                text = "P2P Roleplay",
                style = TypographyP2pTitle,
                color = EchoOnBackground,
                textAlign = TextAlign.Center,
            )
            Spacer(modifier = Modifier.height(10.dp))
            Text(
                text = "Practice with real people in guided scenarios.",
                style = MaterialTheme.typography.bodyMedium,
                color = EchoMuted,
                textAlign = TextAlign.Center,
            )
            Spacer(modifier = Modifier.height(28.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                P2pFeatureCard(
                    modifier = Modifier.weight(1f),
                    title = "SAFE SPACE",
                    body = "Strict community guidelines.",
                )
                P2pFeatureCard(
                    modifier = Modifier.weight(1f),
                    title = "EARN POINTS",
                    body = "Level up your fluency.",
                )
            }
            Spacer(modifier = Modifier.height(28.dp))
            Button(
                onClick = { /* 稍后接匹配 */ },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = EchoOnBackground,
                    contentColor = Color.White,
                ),
            ) {
                Text(
                    "FIND A PARTNER",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

@Composable
private fun P2pFeatureCard(
    modifier: Modifier,
    title: String,
    body: String,
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .border(1.dp, EchoBorder, RoundedCornerShape(14.dp))
            .background(EchoSurface)
            .padding(14.dp),
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
            color = EchoOnBackground,
        )
        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = body,
            style = MaterialTheme.typography.bodySmall,
            color = EchoMuted,
        )
    }
}
