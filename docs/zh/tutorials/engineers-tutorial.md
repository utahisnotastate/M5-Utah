# 电子工程师教程 — 硬件上下文协议

**对象：** 硬件/系统工程师  
**目标：** 在注册表中描述物理单元并验证功耗/时序

## 1. 分层边界

| 层 | 职责 |
|----|------|
| 固件 | 确定性 IO、遥测、ACK、注册表任务监管 |
| m5resolver | 校验、仿真、Agent 修复 |
| Utah-Flux | 可视化 → 意图 |
| 注册表 | 能力、地址、语义动作 |

## 2. 注册新 Unit

编辑 `registry/units.json`，参考 `schemas/registry.schema.json`。

## 3. 语义动作

在 `firmware/src/registry_runtime.cpp` 中映射，例如：

- `ACTION_INDICATE_STATUS_SUCCESS`
- `ACTION_REACT_TO_MOTION`

## 4. 安全门禁

`host/m5resolver/safety.py` 限制频率、功耗、扬声器参数。  
`simulation.py` 在下发前估算电流。

## 5. 上电检查清单

1. 烧录固件，确认 20Hz 遥测
2. 发送 `capability_query`
3. 下发 `registry` 片段
4. 确认 ACK 与物理行为

## 6. 兼容性

见 [兼容性矩阵](../compatibility-matrix.md)。
