# MyEnglishChat Flutter 客户端（Android+iOS）

本目录是 **MyEnglishChat 主客户端**（Flutter，Android + iOS）。

## 1) 先安装 Flutter（Windows）

由于本机当前未检测到 Flutter SDK（`flutter` 命令不存在），请先按官方文档安装并配置环境变量：

- Flutter 安装：`https://docs.flutter.dev/get-started/install/windows`

安装完成后在 PowerShell 验证：

```powershell
flutter --version
flutter doctor
```

## 2) 生成平台工程（第一次）

在仓库根目录执行（会在 `app_flutter/` 生成 `android/`、`ios/` 等平台目录）：

```powershell
cd C:\Users\uip84\AndroidStudioProjects\app_flutter
flutter create .
```

> 说明：我们先把“工程结构与代码骨架”落在仓库里；等 Flutter 装好后再生成平台目录并跑 `flutter analyze` / 构建。

## 3) 运行

```powershell
cd C:\Users\uip84\AndroidStudioProjects\app_flutter
flutter pub get
flutter run
```

### 3.1 真机 / 模拟器的后端地址

默认 debug 会用 `http://10.0.2.2:8088/`（Android 模拟器访问本机）。你可以在启动时覆盖：

```powershell
flutter run --dart-define=BACKEND_BASE_URL=http://192.168.0.59:8088/
```

> iOS 模拟器通常用 `http://127.0.0.1:8088/`；真机用电脑局域网 IP。

## 4) 与后端联调

- 后端：`backend/`（FastAPI）
- Debug 真机联调要注意局域网 IP 与端口，以及 Android/iOS 的网络安全策略（后续会在 Flutter 侧补齐环境配置与说明）。

