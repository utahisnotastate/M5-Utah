# 技术用户指南

## 技术栈（v0.8.2）

| 组件 | 路径 | 作用 |
|------|------|------|
| Utah Flux Studio | `host/utah_flux/studio.py` | 乐高 IDE（8765） |
| **UtahClaw 画布** | `host/utah_flux/static/utah_studio.html` | 意图解析 UI（8024） |
| **全知甲板** | `host/utah_flux/omniscient_daemon.py` | 自动发现（8000） |
| UtahClaw 守护进程 | `host/utah_flux/utahclaw_daemon.py` | Ollama + 串口桥 |
| 场图编译器 | `host/utah_flux/field_compiler.py` | Sanctum `nodes`/`bindings` → 显示意图 |
| m5resolver | `host/m5resolver/` | 意图、类型态、安全线 |
| Omega 防御栈 | `firmware/src/OmegaDefense.*` 等 | 边缘韧性模块 |
| 主权边缘层 | `firmware/src/SovereignEdge.*` 等 | 声明式运行时 |
| 现实基底 | `firmware/src/RealitySubstrate.*` 等 | Class-1 Omega |
| 不朽发现固件 | `firmware/src/ImmortalDiscovery.*` | Core 0 I2C 扫描 |
| 双核内核 | `firmware/` | M5Kernel 运行时 |

## 用户与开发者

- **儿童/创客：** `Start Utah Flux Studio.bat`
- **氛围编程工程师：** `Install UtahClaw.bat` → `Start UtahClaw Studio.bat` + Ollama
- **发现演示：** `launch/Start Omniscient Studio.bat`
- **开发者：** `pip install -e host`、`pytest`、`examples/`
- **Sanctum 场图：** `projects/sanctum.flux.json`（见 [field-graph-compiler.md](field-graph-compiler.md)）

## 完整教程

[技术用户教程](tutorials/technical-tutorial.md)

## 意图模型

键：`display`、`speaker`、`power`、`registry`、`capability_query`、`ephemeral_store`  
见 `schemas/intent.schema.json`

## 安全与仿真

编译前经过 validation、safety、simulation。

## Studio API

- `GET /api/bricks`
- `GET /api/templates`
- `POST /api/compile`

## 遗留 CLI

`m5resolver` CLI 与 `examples/` 供自动化使用，产品用户不需要。
