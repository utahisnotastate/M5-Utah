# Omega 防御栈（一级边缘韧性）

面向 M5Stack CoreS3 的固件加固模块，用于抵御时序侧信道、单节点故障与固件取证提取。通过 `firmware/src/OmegaDefense.cpp` 中的 `omegaDefenseInit()` 与 `omegaDefenseTick()` 集成。

## 模块

| 模块 | 文件 | 作用 |
|------|------|------|
| **布朗盾** | `StochasticShield.*` | ADC + TRNG 热力学时钟抖动，包裹注册表 JSON 分发 |
| **群魂镜像** | `MeshStateMirror.*` | ESP-NOW 拜占庭状态向量（10ms）；ECC 校验；DeepSleep 交接 |
| **失忆内核** | `AmnesiaKernel.*` | 易失 PSRAM 载荷保险库；熵擦除；IMU 地理锚点 |
| **时空调度器** | `ChronoScheduler.*` | 100µs 超频推测任务提交（运动 → 延迟告警） |
| **张量虚空链路** | `TensorVoidLinkage.*` | IRAM 2-bit 量化潜向量对 IMU 评分 |
| **拉撒路守护** | `LazarusDaemon.*` | RTC 快内存启动计数 + panic/WDT 后复活遥测 |

## 启动集成

```
m5IntegratedKernelBoot()
  └── omegaDefenseInit()
        ├── stochasticShieldInit()
        ├── lazarusDaemonInit()
        ├── amnesiaKernelInit()
        ├── meshStateMirrorInit()
        └── chronoSchedulerInit()

M5Kernel 应用循环 (Core 1)
  └── omegaDefenseTick(tick, frames)
```

Core 1 上的注册表 JSON 分发由 `StochasticShield::executeWithBrownianJitter` 包裹。

## 遥测（`omega_*` 字段）

| 字段 | 含义 |
|------|------|
| `omega_tensor_score` | 最近 IRAM 潜向量分数 |
| `omega_chrono_commits` | 已提交的推测任务数 |
| `omega_mesh_peer_updates` | 收到的有效对端状态向量 |
| `omega_mesh_suicide_handoffs` | 触发的 DeepSleep 交接次数 |
| `omega_lazarus_boot_count` | RTC 持久化启动计数 |
| `omega_amnesia_payload_bytes` | 易失保险库中的字节数 |

发送 `{"capability_query": true}` 可查询能力字符串（含 `stochastic_execution_obfuscation` 等六项）。

## 易失意图保险库

仅在易失 RAM 中存储任务参数（永不写入 Flash）：

```json
{
  "ephemeral_store": true,
  "ephemeral": { "mission": "sanctum_alpha", "params": { "threshold": 0.8 } }
}
```

IMU 篡改或地理漂移时，失忆内核对 PSRAM 熵擦除并重启。

## 网状故障转移（多设备）

1. 为两台及以上 CoreS3 刷入相同固件。
2. ESP-NOW 每 10ms 广播状态向量。
3. 校验通过且 `orchestration_tick` 更高的对端向量被采纳。
4. 堆内存危急时，主节点广播最终状态并 DeepSleep；对端接续。

## 设计说明

- **不从 PSRAM 执行任意代码** — 保险库存储 JSON 载荷，供现有意图管道使用。
- **ESP-NOW 优雅降级** — 射频初始化失败时单节点继续运行。
- **拉撒路** 通过 `esp_reset_reason()` + RTC 标志追踪复活，而非脆弱观察点。

## 相关文档

- [固件 README](../../firmware/README.md)
- [架构](architecture.md)
- ADR [0045](../adr/0045-omega-defense-edge-stack.md)
- [主权边缘层](sovereign-edge-tier.md)
