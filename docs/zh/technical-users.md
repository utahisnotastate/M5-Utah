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
