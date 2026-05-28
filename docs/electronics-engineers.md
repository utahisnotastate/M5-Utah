# Electronics Engineer Guide / 电子工程师指南

## 1) Engineering objective / 工程目标

**EN**  
Collapse duplicated software effort across M5Stack hardware variants by:
- stabilizing a thin device runtime
- moving behavior into host-side intent orchestration
- declaring hardware variability in a machine-readable registry

**中文**  
通过以下方式压缩 M5Stack 多硬件变体上的重复软件成本：
- 固化轻量设备运行时
- 将行为逻辑迁移到主机侧意图编排
- 用机器可读注册表描述硬件差异

## 2) Boundary definition / 边界定义

**EN**
- Device firmware responsibilities:
  - deterministic IO execution
  - telemetry acquisition and framing
  - bounded command acknowledgments
- Host runtime responsibilities:
  - policy and behavior
  - reactive signal mapping
  - composition of multi-unit workflows

**中文**
- 设备固件职责：
  - 确定性 IO 执行
  - 遥测采集与封包
  - 有界命令应答
- 主机运行时职责：
  - 策略与行为逻辑
  - 响应式信号映射
  - 多 Unit 工作流组合

## 3) Protocol notes / 协议要点

**EN**
- transport: UART/USB serial @ 115200
- frame type: line-delimited JSON
- uplink: telemetry frames (`type=telemetry`)
- downlink: intent frames (`display`, `speaker`, `power`)
- control feedback: ACK frames (`type=ack`, `ok=true/false`)

**中文**
- 传输：UART/USB 串口 @ 115200
- 帧格式：按行分隔 JSON
- 上行：遥测帧（`type=telemetry`）
- 下行：意图帧（`display`, `speaker`, `power`）
- 控制反馈：ACK 帧（`type=ack`, `ok=true/false`）

## 4) Registry-driven unit modeling / 注册表驱动建模

**EN**
Represent unit variance in `registry/units.json`:
- bus type
- device address
- exposed capabilities
- symbolic register map

This allows one runtime to reason about many units without hardcoding each as a separate repository.

**中文**
在 `registry/units.json` 中表达 Unit 差异：
- 总线类型
- 设备地址
- 对外能力
- 符号化寄存器映射

这让单一运行时可以处理大量 Unit，而不必为每个 Unit 维护独立仓库。

## 5) Performance and power strategy / 性能与功耗策略

**EN**
- Keep MCU loop short and non-blocking.
- Emit telemetry at fixed cadence (currently 20 Hz).
- Route behavior changes event-style in host graph.
- Avoid high-frequency firmware recompiles during algorithm iteration.

**中文**
- MCU 主循环保持短小且非阻塞。
- 固定节拍输出遥测（当前 20 Hz）。
- 在主机图模型中以事件方式路由行为变化。
- 算法迭代期间避免高频固件重编译。

## 6) Reliability posture / 可靠性策略

**EN**
- Prefer explicit fault handling and retries over self-modifying code.
- Keep replayable telemetry logs for diagnosis.
- Validate JSON schema at host boundary.
- Use watchdog and timeout policy per transport link.

**中文**
- 优先采用显式异常处理与重试，而非自修改代码。
- 保留可回放遥测日志用于诊断。
- 在主机边界执行 JSON 模式校验。
- 为链路设置看门狗与超时策略。

## 7) Migration checklist for hardware teams / 硬件团队迁移清单

**EN**
1. Inventory legacy module repos and classify as active/reference/deprecated.
2. Add capability records for each active unit to registry.
3. Port golden-path demos to host runtime intents.
4. Freeze old APIs and publish compatibility notes.
5. Measure iteration latency and defect rate before/after migration.

**中文**
1. 盘点历史模块仓库，并标记为活跃/参考/弃用。
2. 为每个活跃 Unit 在注册表补齐能力记录。
3. 将核心演示迁移到主机端意图流程。
4. 冻结旧 API 并发布兼容说明。
5. 对比迁移前后的迭代时延与缺陷率。
