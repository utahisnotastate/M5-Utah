# 现实基底（Class-1 Omega）

主导物理内存与运动物质的固件模块：RF 动能网状存储、零数学机器人学、环境 IoT 计算、植物计算、空间 UI、因果调试、本征态编译与创世启动锚定。

由 `RealitySubstrate` 协调 — `sovereignEdgeInit()` 之后调用 `realitySubstrateInit()`；`sovereignEdgeTick()` 内调用 `realitySubstrateTick()`。

## 模块（披露 7–14）

| 模块 | 作用 |
|------|------|
| **AkashicFileSystem** | 文件碎片化为 ESP-NOW 射频飞行；驻波重广播（无 SD/Flash） |
| **ChronoKinetic** | 黄金比例 PWM 舵机松弛（无 PID） |
| **MnemonicProxy** | 混杂模式 WiFi 蜂群扫描 + 环境 ESP-NOW 张量分发 |
| **BiosymmetricBus** | DAC/ADC 有机激活（植物计算基底） |
| **SpatialUI** | 关背光磁通量投影（意图门控） |
| **CausalDebugger** | setjmp 概率护盾；避免崩溃遥测 |
| **EigenStateCompiler** | Flux 意图坍缩进易失保险库 |
| **GenesisProtocol** | 上电启动 RTC 世代锚定 |

## 意图 API

```json
{"akashic_inject": true, "akashic_file_id": 42, "akashic": "任务载荷"}
{"eigen_collapse": true, "flux_intent": "{...}"}
{"spatial_ui": true}
{"chrono_kinetic": {"target": 45.0}}
```

## 遥测（`substrate_*`）

见英文版字段表 [reality-substrate.md](../en/reality-substrate.md)（中英同步）。

## ESP-NOW 网状解复用

| 包类型 | 处理器 |
|--------|--------|
| `0xAF` | Akashic 碎片 |
| `0x4D` | Mnemonic 任务（出站） |
| `ExecutionFrame` | SwarmSoul |
| `MeshStateVector` | MeshStateMirror |

## 设计说明

- 无 `std::vector` — 固定碎片池
- **SpatialUI** 仅在 `spatial_ui: true` 时关闭背光
- **GenesisProtocol** 记录 RTC 世代 — 不绕过 FreeRTOS
- **MnemonicProxy** 仅本地扫描

## 相关文档

- [主权边缘层](sovereign-edge-tier.md)
- [Omega 防御栈](omega-defense-stack.md)
- ADR [0047](../adr/0047-reality-substrate-class1.md)
