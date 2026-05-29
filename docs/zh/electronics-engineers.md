# 电子工程师指南

## 职责

在注册表中定义总线、地址、能力、功耗与语义动作。

## 完整教程

[工程师教程](tutorials/engineers-tutorial.md)

## 固件

- 意图执行与 ACK
- 注册表热更新与任务监管（`registry_runtime.cpp`）
- 遥测含 `status`、`metrics.free_heap`

## 主机端

策略、可视化编译、校验、Agent — 不在固件堆业务逻辑。

## 协议

串口 115200，按行 JSON。

## 迁移

新 Unit 进注册表，避免为每个 SKU 新建命令式驱动仓库。
