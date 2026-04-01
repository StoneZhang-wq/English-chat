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

默认 debug 会用 `http://10.0.2.2:8088/`（**仅** Android 模拟器访问本机）。**物理手机**必须改为电脑的局域网 IP，例如：

```powershell
flutter run --dart-define=BACKEND_BASE_URL=http://192.168.0.59:8088/
```

**Android Studio**：**Run → Edit Configurations** → 选中你的 Flutter 配置 → **Additional run arguments** 填同上 `--dart-define=...`（改 IP 后需 **Stop 再 Run**，编译期常量才会更新）。

**明文 HTTP**：`debug` / `profile` 构建已在 **`android/app/src/debug|profile/AndroidManifest.xml`** 合并 **`usesCleartextTraffic`**，真机访问 `http://192.168.x.x:8088` 不会被默认策略拦掉。

> iOS 模拟器通常用 `http://127.0.0.1:8088/`；iOS 真机同样要用局域网 IP，并在需要时配置 **App Transport Security**（INFO.plist）。

## 4) 与后端联调

- 后端：`backend/`（FastAPI），默认监听 `0.0.0.0:8088`，手机与电脑须在同一 Wi‑Fi；Windows 防火墙需放行 **8088** 入站。
- 可在手机浏览器打开 `http://<电脑IP>:8088/docs` 确认网络可达。

