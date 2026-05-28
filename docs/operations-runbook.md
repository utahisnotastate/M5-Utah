# Operations Runbook / 运维手册

## Runtime health checks / 运行健康检查

**EN**
- Verify device enumerates on expected serial port.
- Confirm telemetry appears at steady cadence.
- Send smoke-test intent and validate ACK response.
- Check battery/charging fields for sane values.

**中文**
- 确认设备在预期串口出现。
- 确认遥测按稳定节拍输出。
- 发送冒烟测试意图并验证 ACK 响应。
- 检查电池/充电字段是否合理。

## Incident response / 事故响应

**EN**
1. Capture raw serial logs.
2. Record firmware hash and host package version.
3. Attempt controlled restart sequence.
4. Isolate whether failure is transport, parsing, or intent logic.
5. File issue with reproduction and logs.

**中文**
1. 采集原始串口日志。
2. 记录固件哈希与主机包版本。
3. 执行可控重启流程。
4. 判断故障属于链路、解析还是意图逻辑层。
5. 携带复现步骤与日志提交问题单。
