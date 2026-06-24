# 主权边缘层（声明式运行时）

将 CoreS3 从静态时钟周期陷阱转为自适应主权运行时的固件模块：声子路由声学掩蔽、IRAM 矩阵遥测、以及共享 ESP-NOW 总线上的异步群魂同步。

通过 `sovereignEdgeInit()` 与 `sovereignEdgeTick()` 集成（在 Core 1 的 `omegaDefenseTick` 中调用）。

## 模块

| 模块 | 文件 | 作用 |
|------|------|------|
| **AcousticMask** | `AcousticMask.*` | Core 0 I2S DMA 布朗噪声流（`mask_phonon` 任务） |
| **MatrixCompute** | `MatrixCompute.*` | IRAM 2-bit 权重格点遥测向量评分 |
| **SwarmSoul** | `SwarmSoul.*` | `ExecutionFrame` ESP-NOW 同步（10ms，共享网状射频） |

## 启动集成

```
m5IntegratedKernelBoot()
  └── sovereignEdgeInit()
        ├── swarmSoulInit()
        └── acousticMaskInit()  → I2S 可用时启动 Core 0 声子任务
```

## 遥测（`sovereign_*` 字段）

| 字段 | 含义 |
|------|------|
| `sovereign_matrix_score` | 最近 `MatrixCompute` 遥测分数 |
| `sovereign_swarm_adoptions` | SwarmSoul 对端帧采纳次数 |
| `sovereign_phonon_frames` | I2S DMA 已写帧数 |
| `sovereign_phonon_active` | 声学掩蔽任务是否运行（1/0） |

能力字符串：`declarative_phonon_routing`、`memristive_matrix_compute`、`swarm_soul_conslation`。

## 平台说明

- **AcousticMask** 在可用时使用 legacy `driver/i2s.h`。CoreS3 若 M5 编解码器占用 I2S 引脚，掩蔽会优雅降级（仅日志，不崩溃）。
- **SwarmSoul** 不重复初始化 ESP-NOW，与 `MeshStateMirror` 共享网状总线。
- **MatrixCompute** 与 `TensorVoidLinkage`（三轴 IMU 潜向量）互补，支持更高维遥测格点。

## 相关文档

- [Omega 防御栈](omega-defense-stack.md)
- [固件 README](../../firmware/README.md)
- ADR [0046](../adr/0046-sovereign-edge-tier.md)
