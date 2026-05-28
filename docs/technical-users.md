# Technical User Guide / 技术用户指南

## 1) What this project is / 项目是什么

**EN**  
M5 Resolver Substrate is a consolidation layer for M5Stack development:
- one universal firmware image
- one host runtime
- one registry for hardware capability metadata
- one reactive intent pipeline

It replaces repetitive per-device imperative code with declarative intent messages and registry-backed mappings.

**中文**  
M5 Resolver Substrate 是面向 M5Stack 开发的整合层：
- 一个通用固件镜像
- 一个主机端运行时
- 一个硬件能力元数据注册表
- 一条响应式意图处理链路

它用声明式意图消息与注册表驱动映射，替代重复的“每设备单独命令式代码”。

## 2) Core architecture / 核心架构

**EN**
- `firmware/src/main.cpp`: JSON intent interpreter running on device
- `host/m5resolver/controller.py`: serial transport
- `host/m5resolver/fluxwire.py`: telemetry->intent reactive mappings
- `host/m5resolver/registry.py`: dynamic unit specs from JSON
- `registry/units.json`: capability and protocol metadata

Data loop:
1. firmware streams telemetry
2. host parses frames
3. FluxGraph maps source values into intent patches
4. host sends intents back
5. firmware applies intents to display/audio/power

**中文**
- `firmware/src/main.cpp`：设备端 JSON 意图解释器
- `host/m5resolver/controller.py`：串口传输层
- `host/m5resolver/fluxwire.py`：遥测到意图的响应式映射
- `host/m5resolver/registry.py`：从 JSON 动态加载单元规格
- `registry/units.json`：能力与协议元数据

数据循环：
1. 固件推送遥测
2. 主机解析帧
3. FluxGraph 将源值映射为意图补丁
4. 主机回传意图
5. 固件执行显示/音频/电源操作

## 3) Quick setup / 快速配置

**EN**
1. Flash firmware
   - `cd firmware`
   - `pio run -t upload`
2. Install host package
   - `cd host`
   - `pip install -e .`
3. Run example
   - `cd ..`
   - `python examples/tilt_tone.py --port COM3`

**中文**
1. 烧录固件
   - `cd firmware`
   - `pio run -t upload`
2. 安装主机包
   - `cd host`
   - `pip install -e .`
3. 运行示例
   - `cd ..`
   - `python examples/tilt_tone.py --port COM3`

## 4) Intent schema reference / 意图结构参考

**EN**
Current supported top-level keys:
- `display`
  - `clear`, `bg_color`
  - `text` (`x`, `y`, `size`, `color`, `payload`)
- `speaker`
  - `tone` (`frequency`, `duration`, `channel`)
  - `stop`
- `power`
  - `led`
  - `off`

Example:
```json
{
  "display": {
    "clear": true,
    "bg_color": 0,
    "text": { "x": 8, "y": 24, "size": 2, "color": 65535, "payload": "Hello" }
  },
  "speaker": { "tone": { "frequency": 660, "duration": 80, "channel": 0 } }
}
```

**中文**
当前支持的顶层键：
- `display`
  - `clear`, `bg_color`
  - `text`（`x`, `y`, `size`, `color`, `payload`）
- `speaker`
  - `tone`（`frequency`, `duration`, `channel`）
  - `stop`
- `power`
  - `led`
  - `off`

## 5) Extending the registry / 扩展注册表

**EN**
Add a new unit into `registry/units.json`:
1. choose `unit_id`
2. define `bus` and `address`
3. list `capabilities`
4. add `register_map` symbols

Then load from code:
```python
from m5resolver import DriverRegistry
reg = DriverRegistry("registry/units.json")
reg.load()
print(reg.list_ids())
```

**中文**
在 `registry/units.json` 添加新 Unit：
1. 选择 `unit_id`
2. 定义 `bus` 与 `address`
3. 填写 `capabilities`
4. 添加 `register_map` 符号

随后在代码中加载：
```python
from m5resolver import DriverRegistry
reg = DriverRegistry("registry/units.json")
reg.load()
print(reg.list_ids())
```

## 6) Migration guidance for developers / 开发者迁移建议

**EN**
- Treat old per-module libraries as compatibility references.
- Move new feature work into host intent logic first.
- Keep firmware minimal and stable; avoid business logic in firmware.
- Encode unit differences into registry metadata, not custom forks.

**中文**
- 将旧的“按模块划分库”视为兼容参考。
- 新功能优先写在主机端意图逻辑中。
- 固件保持最小且稳定；避免在固件中堆叠业务逻辑。
- 用注册表元数据表达差异，不再通过大量分叉库维护。

## 7) Troubleshooting / 故障排查

**EN**
- No serial frames: verify baud (`115200`) and correct port.
- No telemetry type: ensure firmware flashed from this repo.
- No sound: check board speaker support and volume.
- Unexpected JSON parse failures: ensure newline-terminated JSON payloads.

**中文**
- 无串口帧：确认波特率 `115200` 与端口正确。
- 无 telemetry 类型：确认使用本仓库固件。
- 无声音：确认板卡扬声器支持和音量设置。
- JSON 解析失败：确认每条 JSON 以换行结尾。
