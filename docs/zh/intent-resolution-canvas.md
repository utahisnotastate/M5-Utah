# 意图解析画布 — UtahClaw 全知工作室

**文件：** `host/utah_flux/static/utah_studio.html`（仓库根目录亦有 `utah_studio.html`）

## 启动方式

| 方式 | 命令 |
|------|------|
| 一次性安装 | `Install UtahClaw.bat` |
| Windows 启动器 | `Start UtahClaw Studio.bat`（根目录）或 `launch/Start UtahClaw Studio.bat` |
| 命令行 | `utah-claw-studio` 或 `py -m utah_flux.utahclaw_daemon` → http://127.0.0.1:8024 |
| 独立 HTML | 先启动守护进程，再打开 `utah_studio.html` |

## 依赖

- `pip install -e "./host[claw]"`（或 `Install UtahClaw.bat`）
- Ollama 已拉取 `llama3` 模型
- 已刷写含 Omega 防御栈的 CoreS3 固件（仅需一次）

完整指南见 [utah-claw-studio.md](utah-claw-studio.md) 或英文版 [../en/utah-claw-studio.md](../en/utah-claw-studio.md)。
