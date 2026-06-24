# 运维手册

## UtahClaw 全知工作室健康检查

1. 一次性运行 `Install UtahClaw.bat`（安装 `host[claw]`：FastAPI、Uvicorn、Ollama 客户端）。
2. 本地已运行 `ollama run llama3`。
3. 双击 `Start UtahClaw Studio.bat` → `http://127.0.0.1:8024`。
4. **UtahClaw Daemon** 控制台窗口保持打开（守护进程在此运行）。
5. 状态显示 **NEURAL LINK STABLE**。
6. 插入 CoreS3 USB — 代理面板显示 `Linked: COMx`（先关闭 Ghost Forge / 串口监视器）。
7. Grove A 口接 ENV III — 硬件甲板显示自动识别。
8. 输入意图 → **MANIFEST** — 代理面板显示已部署 JSON/代码。

### UtahClaw 故障

| 问题 | 处理 |
|------|------|
| `ERR_CONNECTION_REFUSED` | 守护进程崩溃 — 查看 Daemon 窗口；重新 `Install UtahClaw.bat` |
| 缺少 `fastapi` | 在仓库根目录 `pip install -e "./host[claw]"` |
| COM 口冲突 | 同一 COM 只能被一个程序占用 |

## 全知发现甲板

1. `pip install -e "host[daemon]"`
2. `launch/Start Omniscient Studio.bat` → `http://127.0.0.1:8000`
3. I2C 设备响应后显示发现卡片

## Utah Flux Studio 健康检查

1. 双击 `Start Utah Flux Studio.bat` → 打开 `http://127.0.0.1:8765`
2. Hello 模板 → 编译状态 **Ready to play**
3. **Connect Device** → **Connected**
4. **Play** → Live Log 有遥测

## 设备检查

1. 串口可见
2. 约 50ms 一帧遥测 JSON
3. 意图后 ACK：`ok: true`

## 故障处理

1. 导出 Live Log
2. 保存客户 `.flux.json`
3. 记录固件与包版本
4. 用相同模板复现
5. 附日志提 issue

## 终端用户策略

支持只引导 GUI 操作，不要求命令行。
