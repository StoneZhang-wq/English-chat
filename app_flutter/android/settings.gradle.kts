import java.io.File
import java.util.Properties

/**
 * [CXX1300] `flutter_kitten_tts` 的 Gradle 脚本要求 CMake 3.18.1 目录；本机常只有 3.22+/4.x。
 * 在配置子工程前写入 `local.properties` 的 `cmake.dir`，指向 **已存在的** SDK CMake 安装。
 */
fun ensureAndroidCmakeDirInLocalProperties(settingsRoot: File) {
    val lp = File(settingsRoot, "local.properties")
    if (!lp.exists()) return
    val props = Properties()
    lp.inputStream().use { props.load(it) }
    val sdkDirPath = props.getProperty("sdk.dir") ?: return
    val sdkDir = File(sdkDirPath)
    val cmakeRoot = File(sdkDir, "cmake")
    if (!cmakeRoot.isDirectory) return

    fun File.hasCmake(): Boolean {
        return File(this, "bin/cmake.exe").exists() || File(this, "bin/cmake").exists()
    }

    val preferred = listOf("3.18.1", "3.22.1", "4.1.2")
    val chosen = preferred
        .map { File(cmakeRoot, it) }
        .firstOrNull { it.isDirectory && it.hasCmake() }
        ?: cmakeRoot.listFiles()
            ?.filter { it.isDirectory && it.hasCmake() }
            ?.maxByOrNull { it.name }

    if (chosen == null) return
    val want = chosen.absolutePath.replace('\\', '/')
    if (props.getProperty("cmake.dir") == want) return

    val lines = lp.readText().lines().filterNot { it.trim().startsWith("cmake.dir=") }
    val body = lines.joinToString("\n").trimEnd()
    lp.writeText(
        if (body.isEmpty()) "cmake.dir=$want\n"
        else "$body\ncmake.dir=$want\n",
    )
}

ensureAndroidCmakeDirInLocalProperties(file("."))

pluginManagement {
    val flutterSdkPath =
        run {
            val properties = java.util.Properties()
            file("local.properties").inputStream().use { properties.load(it) }
            val flutterSdkPath = properties.getProperty("flutter.sdk")
            require(flutterSdkPath != null) { "flutter.sdk not set in local.properties" }
            flutterSdkPath
        }

    includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    id("com.android.application") version "8.11.1" apply false
    id("org.jetbrains.kotlin.android") version "2.2.20" apply false
}

include(":app")
