# UtahClaw 全知工作室

**意图解析画布（Intent-Resolution Canvas）** 是一个零依赖 HTML 界面，通过 WebSocket 连接本地 UtahClaw 守护进程。无需云端 API，无需 npm 构建 — 只需 Chromium 浏览器和本机回环网络。

## 快速开始（推荐）

1. 一次性安装：
   ```text
   pip install -e "host[claw]"
   ollama run llama3
   ```
2. 固件只需刷写一次「不朽引导程序」（见 [architecture.md](architecture.md)）。
3. 双击 **`launch/Start UtahClaw Studio.bat`**（或运行 `utah-claw-studio`）。
4. 浏览器打开 **http://127.0.0.1:8024** 进入实时画布。

## 界面说明

| 面板 | 作用 |
|------|------|
| **硬件甲板** | 不朽 I2C 自动发现的 Grove 模块 |
| **硅遥测** | M5Stack 原始串口输出 |
| **UtahClaw 控制台** | 本地 Llama-3 回复与自动修复事件 |
| **MANIFEST** | 用自然语言发送意图 → JSON/代码 → 设备 |

## 独立 HTML 文件

仓库根目录的 `utah_studio.html` 可直接打开，但须**先启动 UtahClaw 守护进程**：

```text
utah-claw-studio
```

然后双击 `utah_studio.html` 或访问 http://127.0.0.1:8024。

以 `file://` 打开时，画布默认连接 `ws://127.0.0.1:8024/ws/studio`。

## WebSocket 协议

**浏览器 → 守护进程：**

```json
{"type": "vibe_request", "intent": "让屏幕变红"}
```

**守护进程 → 浏览器：**

| `type` | 含义 |
|--------|------|
| `log` | 串口遥测行 |
| `agent` | UtahClaw 状态或生成代码 |
| `discovery` | Grove 传感器插拔（`data` 对象） |

## 自动修复循环

当串口输出匹配错误模式（`Traceback`、`SyntaxError`、`Guru Meditation` 等）时，UtahClaw 会：

1. 在代理面板通知用户
2. 将错误发给本地 Ollama
3. 向设备推送修正后的 JSON 或 MicroPython 粘贴模式代码

## 隐私与商业化定位

- **完全离线** — 原理图与意图不离开本机
- 适合 **Sovereign Foundry** 打包（PyInstaller `.exe` + 预刷 CoreS3 套件）
- 面向注重隐私的团队、STEM 实验室、隔离网络环境

## 相关文档

- [全知发现工作室](omniscient-studio.md) — 仅硬件发现（无 LLM）
- [架构](architecture.md) — 不朽引导程序与双核内核
- ADR [0044](../adr/0044-immortal-bootloader-autonomic-discovery.md)
