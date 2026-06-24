# m5-utah 架构（中文摘要）

Utah Flux Studio / **m5-utah** 是面向 M5Stack 的**意图优先**控制平面：主机 Python 将对话与声明式意图编译为线路格式；ESP32 固件通过双核微内核执行。

完整英文版：[architecture.md](../en/architecture.md)

## 系统概览

```
主机 (Python)          串口 / Fluxwire           固件 (ESP32)
IntentController  ──►  CrossCorePipe (Core 0)  ──►  注册表与单元
UtahClaw 画布     ◄──  JSON 发现 / 遥测        ◄──  不朽 I2C 扫描
```

## 双核 m5-kernel

| 核心 | 角色 |
|------|------|
| **Core 0** | 协议引擎：串口摄取、二进制帧、`#A` 安全线、不朽 I2C 发现 |
| **Core 1** | 编排引擎：环形缓冲、意图分发、遥测、自愈 |

`setup()` 调用 `m5IntegratedKernelBoot()`；Arduino `loop()` 挂起，应用逻辑在 Core 1 任务中运行。

## 不朽引导程序（v0.8+）

**刷写一次，永久意图虚拟机。**

- `ImmortalDiscovery` 每 500ms 扫描 Grove A 口 I2C
- 发出 `discovery` / `disconnect` JSON 事件
- 主机 `HardwareMatrix` 自动锁定 Espressif USB（VID `303A`）

## 安全与形式验证

| 模块 | 作用 |
|------|------|
| `typestate.py` | 主机预检：非法状态转移拒绝下发 |
| `secure_wire.py` | `#A` 单调序列防重放 |
| `OtaRollbackFence` | 双缓冲 OTA 回滚 |

## 开发者界面

| 工具 | 端口 | 说明 |
|------|------|------|
| Utah Flux Studio | 8765 | 乐高积木 IDE（儿童向） |
| 全知工作室 | 8000 | 硬件自动发现甲板 |
| UtahClaw 画布 | 8024 | 离线氛围编程 + 自动修复 |
| Vibe 网关 | 8023 | WebUSB 浏览器 IDE |

## Omega 防御栈（v0.8.2）

| 模块 | 作用 |
|------|------|
| `StochasticShield` | 注册表分发路径上的 ADC + TRNG 抖动 |
| `MeshStateMirror` | ESP-NOW 10ms 拜占庭向量 + DeepSleep 交接 |
| `AmnesiaKernel` | PSRAM 易失保险库 + IMU 篡改擦除 |
| `ChronoScheduler` | 100µs 推测任务提交 |
| `TensorVoidLinkage` | IRAM 2-bit 潜向量评分 |
| `LazarusDaemon` | RTC 复活遥测 |

详见 [omega-defense-stack.md](omega-defense-stack.md) · ADR [0045](../adr/0045-omega-defense-edge-stack.md)

## 场图编译器（v0.8.2）

`nodes`/`bindings` 格式项目由 `host/utah_flux/field_compiler.py` 编译；绑定保留在主机侧。见 [field-graph-compiler.md](field-graph-compiler.md)。

## 主权边缘层（v0.8.3）

| 模块 | 作用 |
|------|------|
| `AcousticMask` | Core 0 I2S 布朗声子 DMA 掩蔽 |
| `MatrixCompute` | IRAM 缓存边界遥测评分 |
| `SwarmSoul` | `ExecutionFrame` ESP-NOW 群魂同步 |

详见 [sovereign-edge-tier.md](sovereign-edge-tier.md) · ADR [0046](../adr/0046-sovereign-edge-tier.md)

## 统一生命周期

```
编译 → 校验(typestate) → 安全封装(#A) → 传输 → Core 0 摄取 → 环形缓冲 → Core 1 执行 → 观测
```

## 相关 ADR

- [0040 统一内核入口](../adr/0040-unified-m5-kernel-entry-point.md)
- [0041 类型态与 OTA 回滚](../adr/0041-typestate-enforcement-ota-rollback-fence.md)
- [0043 安全线防重放](../adr/0043-secure-wire-anti-replay-fence.md)
- [0044 不朽引导与自动发现](../adr/0044-immortal-bootloader-autonomic-discovery.md)
