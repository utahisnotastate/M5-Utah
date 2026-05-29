# 技术用户指南

## 技术栈（v0.3+）

| 组件 | 路径 | 作用 |
|------|------|------|
| Utah Flux Studio | `host/utah_flux/studio.py` | 浏览器 GUI |
| Utah-Flux | `host/utah_flux/` | 积木、编译器、模板 |
| m5resolver | `host/m5resolver/` | 意图、安全、Agent |
| 固件 | `firmware/` | 设备运行时 |
| 模式 | `schemas/` | 硬件上下文协议 |

## 用户与开发者

- **终端用户：** 仅双击 `Start Utah Flux Studio.bat`
- **开发者：** `pip install -e host`、`pytest`、可选 `examples/agent_loop.py`

## 完整教程

[技术用户教程](tutorials/technical-tutorial.md)

## 意图模型

键：`display`、`speaker`、`power`、`registry`、`capability_query`  
见 `schemas/intent.schema.json`

## 安全与仿真

编译前经过 validation、safety、simulation。

## Studio API

- `GET /api/bricks`
- `GET /api/templates`
- `POST /api/compile`

## 遗留 CLI

`m5resolver` CLI 与 `examples/` 供自动化使用，产品用户不需要。
