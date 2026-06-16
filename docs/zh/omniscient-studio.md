# 全知工作室（自动发现甲板）

轻量级**硬件发现**界面，无需本地大模型。适合只想在插入 Grove 传感器后立即在屏幕上看到识别结果的场景。

## 快速开始

```text
pip install -e "host[daemon]"
```

双击 **`launch/Start Omniscient Studio.bat`** 或运行：

```text
utah-flux-omniscient
```

打开 **http://127.0.0.1:8000**。

## 工作原理

1. `HardwareMatrix` 扫描 USB，查找 Espressif VID `303A`（CoreS3 原生 USB）。
2. 以 115200 波特率打开串口。
3. 不朽引导程序在 Grove A 口 I2C 扫描时发出 JSON 发现事件。
4. WebSocket `/ws/telemetry` 将事件推送到浏览器甲板。

## WebSocket 事件

| 载荷 | 含义 |
|------|------|
| `{"status":"IMMORTAL_KERNEL_LINKED","port":"COMx"}` | 设备已连接 |
| `{"status":"AWAITING_HARDWARE"}` | 未找到 CoreS3 |
| `{"event":"discovery","unit":"ENV_III_SENSOR",...}` | 传感器插入 |
| `{"event":"disconnect",...}` | 传感器拔出 |

## UtahClaw 与全知对比

| 功能 | 全知 (`:8000`) | UtahClaw (`:8024`) |
|------|----------------|---------------------|
| 自动 USB 扫描 | 是 | 是 |
| I2C 发现甲板 | 是 | 是 |
| 氛围编程 / Ollama | 否 | 是 |
| 错误自动修复 | 否 | 是 |
| 画布 UI | `omniscient.html` | `utah_studio.html` |

课堂演示传感器用**全知**；完整意图工作流用 **UtahClaw**。

## 相关文档

- [UtahClaw 工作室](utah-claw-studio.md)
- ADR [0044](../adr/0044-immortal-bootloader-autonomic-discovery.md)
