package com.example.englishchat.ui

import android.net.Uri
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.englishchat.ui.components.EchoBottomBar
import com.example.englishchat.ui.screens.AiDialogueScreen
import com.example.englishchat.ui.screens.P2pScreen
import com.example.englishchat.ui.screens.ScenarioSessionScreen
import com.example.englishchat.ui.screens.ShadowingScreen
import com.example.englishchat.ui.theme.MyEnglishChatApplicationTheme

object AppRoute {
    const val Shadowing = "shadowing"
    const val AiDialogue = "ai_dialogue"
    const val P2p = "p2p"
    const val ShadowingSession = "shadowing_session"
}

@Composable
fun MainScreen() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val destRoute = navBackStackEntry?.destination?.route.orEmpty()
    // 场景详情页仍属「第一板块 Shadowing」，底栏保持 Shadowing 选中
    val tabRouteForBottomBar =
        if (destRoute.startsWith(AppRoute.ShadowingSession)) AppRoute.Shadowing
        else destRoute.ifEmpty { AppRoute.Shadowing }

    Scaffold(
        bottomBar = {
            EchoBottomBar(
                currentRoute = tabRouteForBottomBar,
                onNavigate = { route ->
                    navController.navigate(route) {
                        popUpTo(AppRoute.Shadowing) {
                            saveState = true
                        }
                        launchSingleTop = true
                        restoreState = true
                    }
                },
            )
        },
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = AppRoute.Shadowing,
            modifier = Modifier.padding(innerPadding),
        ) {
            composable(AppRoute.Shadowing) {
                ShadowingScreen(
                    onScenarioClick = { title ->
                        navController.navigate(
                            "${AppRoute.ShadowingSession}/${Uri.encode(title)}",
                        )
                    },
                )
            }
            composable(
                route = "${AppRoute.ShadowingSession}/{scenarioTitle}",
                arguments = listOf(
                    navArgument("scenarioTitle") { type = NavType.StringType },
                ),
            ) { entry ->
                val encoded = entry.arguments?.getString("scenarioTitle").orEmpty()
                val title = Uri.decode(encoded)
                ScenarioSessionScreen(
                    scenarioTitle = title,
                    onBack = { navController.popBackStack() },
                    onGenerateReview = { /* 后续接生成复习资料 */ },
                )
            }
            composable(AppRoute.AiDialogue) { AiDialogueScreen() }
            composable(AppRoute.P2p) { P2pScreen() }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun MainScreenPreview() {
    MyEnglishChatApplicationTheme {
        MainScreen()
    }
}
