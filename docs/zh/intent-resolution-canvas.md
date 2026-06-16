# 意图解析画布 — UtahClaw 全知工作室

**文件：** `host/utah_flux/static/utah_studio.html`（仓库根目录亦有 `utah_studio.html`）

## 启动方式

| 方式 | 命令 |
|------|------|
| Windows 启动器 | `launch/Start UtahClaw Studio.bat` |
| 命令行 | `utah-claw-studio` → http://127.0.0.1:8024 |
| 独立 HTML | 先启动守护进程，再打开 `utah_studio.html` |

## 依赖

- `pip install -e "host[claw]"`
- Ollama 已拉取 `llama3` 模型
- 已刷写不朽引导程序固件的 M5Stack CoreS3（仅需一次）

完整指南见 [utah-claw-studio.md](utah-claw-studio.md) 或英文版 [../en/utah-claw-studio.md](../en/utah-claw-studio.md)。
