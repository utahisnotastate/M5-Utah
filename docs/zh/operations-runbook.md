# 运维手册

## Studio 健康检查

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
