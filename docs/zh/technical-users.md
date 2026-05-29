# 技术用户指南

## 项目定位

M5 Resolver Substrate 将 M5Stack 开发统一为：

- 一个通用固件运行时
- 一个主机运行时（`m5resolver`）
- 一个注册表（`registry/units.json`）
- 一套意图驱动控制模型

## 快速开始

1. 在 `firmware/` 中烧录固件
2. 在 `host/` 中安装 Python 包
3. 运行 `python examples/tilt_tone.py --port COM3`

## 意图模型

当前支持的意图顶层键：

- `display`
- `speaker`
- `power`

协议定义位于 `schemas/intent.schema.json`。

## 开发建议

- 固件保持确定性和最小化。
- 行为逻辑放在主机侧映射层。
- 通过注册表扩展设备，而不是复制分叉仓库。

## Vibe-IDE 与 Agent 闭环

- 启动网关：`m5vibe`
- 浏览器通过 `/generate_intent` 将自然语言编译为意图 JSON
- `AgenticController` 负责校验、仿真，并可在异常时自动修复
- 固件支持 `registry` 热更新，无需重编译 C++ 行为逻辑
