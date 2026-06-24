# 中文文档

## 从这里开始

**Utah Flux Studio** — 双击仓库根目录的 `Start Utah Flux Studio.bat`。

## 指南与教程

| 受众 | 指南 | 分步教程 |
|------|------|----------|
| 儿童 | [children.md](children.md) | [tutorials/children-tutorial.md](tutorials/children-tutorial.md) |
| 家长/非技术 | [non-technical-users.md](non-technical-users.md) | [tutorials/non-technical-tutorial.md](tutorials/non-technical-tutorial.md) |
| 开发者 | [technical-users.md](technical-users.md) | [tutorials/technical-tutorial.md](tutorials/technical-tutorial.md) |
| 电子工程师 | [electronics-engineers.md](electronics-engineers.md) | [tutorials/engineers-tutorial.md](tutorials/engineers-tutorial.md) |
| M5Stack 员工 | [m5stack-employee-migration-playbook.md](m5stack-employee-migration-playbook.md) | [tutorials/employee-tutorial.md](tutorials/employee-tutorial.md) |

## 运维

- [operations-runbook.md](operations-runbook.md)
- [compatibility-matrix.md](compatibility-matrix.md)
- [github-governance-setup.md](github-governance-setup.md)

## 工作室（v0.8+）

| 工作室 | 启动器 | 指南 |
|--------|--------|------|
| Utah Flux 乐高 IDE | `Start Utah Flux Studio.bat` | — |
| 全知发现甲板 | `launch/Start Omniscient Studio.bat` | [omniscient-studio.md](omniscient-studio.md) |
| UtahClaw 意图画布 | `Start UtahClaw Studio.bat` | [utah-claw-studio.md](utah-claw-studio.md) · [intent-resolution-canvas.md](intent-resolution-canvas.md) |
| 系统架构 | — | [architecture.md](architecture.md) |
| Omega 防御栈（固件） | 刷写一次 | [omega-defense-stack.md](omega-defense-stack.md) |
| 主权边缘层 | 刷写一次 | [sovereign-edge-tier.md](sovereign-edge-tier.md) |
| 现实基底（Class-1） | 刷写一次 | [reality-substrate.md](reality-substrate.md) |
| 场图 / Sanctum | `field_compiler.py` | [field-graph-compiler.md](field-graph-compiler.md) |

## 功能（v0.8.4）

- 可视化乐高 IDE（终端用户无需命令行）
- **不朽引导程序** — 固件只刷一次，I2C 永久自动发现
- **UtahClaw 画布** — 离线 Llama-3 氛围编程 + 串口自动修复
- **全知甲板** — 免驱动 Espressif USB 扫描 + 实时传感器卡片
- **Omega 防御栈** — 抖动、网状镜像、PSRAM 保险库、时序/张量/拉撒路模块
- **主权边缘层** — 声子掩蔽、IRAM 矩阵、群魂同步帧
- **现实基底** — Akashic 射频存储、时序动能、记忆代理蜂群、生物对称、空间 UI、因果调试、本征编译、创世锚定
- **场图编译器** — `nodes`/`bindings` Sanctum 项目 → 显示意图
- 形式类型态校验与 m5-secure 防重放安全线
- 实时终端状态仪表板（`enable_dashboard=True`）
- 意图驱动控制（`display`、`speaker`、`power`、`registry`）
- 安全校验、Agent 自愈、HCP 注册表
- 入门模板与 `.flux.json` 项目保存/打开
