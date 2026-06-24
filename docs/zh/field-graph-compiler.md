# 场图编译器（Sanctum / 节点 + 绑定）

部分项目使用**场图**布局（`nodes`、`bindings`、`layout`），而非经典乐高 `bricks` + `links` 格式。主机编译器 `host/utah_flux/field_compiler.py` 将其转换为设备安全的显示意图。

## 适用场景

| 格式 | 键 | 工具 | 编译器 |
|------|-----|------|--------|
| 乐高积木 | `bricks`, `links` | Utah Flux Studio GUI | `utah_flux/compiler.py` |
| 场图 | `nodes`, `bindings` | 外部注入器或 API | `utah_flux/field_compiler.py` |

示例：`projects/sanctum.flux.json` — 多元素 UI，IMU 驱动标签颜色。

## 编译流程

1. **检测** — `is_field_graph_flux()` 在存在 `nodes`/`bindings` 且无 `bricks` 时为真。
2. **布局** — `layout.type`（如 `Sanctum_Voxel_Alpha`）决定元素位置。
3. **显示意图** — 节点变为 `display.elements[]`（标签、矩形、状态芯片）。
4. **绑定** — 连线表达式保留在**主机侧**，不编译为固件 `registry` 单元。
5. **校验** — validation、safety、simulation 三道关卡。

## 颜色处理

`#FF0000` 等十六进制颜色通过 `rgb888_to_rgb565()` 转为 RGB565（`0xF800`），适配 M5 显示屏硬件。

## 仅主机绑定

如 `imu_coherence → status_label.color` 的绑定在主机根据实时遥测求值，**不会**下发为设备 `registry` 块（避免多余沙箱单元与 CoreS3 崩溃）。

## 测试

```text
py -m pytest tests/test_field_compiler.py -q
```

## 相关文档

- `projects/sanctum.flux.json`
- [技术用户](technical-users.md)
- [Omega 防御栈](omega-defense-stack.md)
