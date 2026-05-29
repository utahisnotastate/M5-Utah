# 技术用户教程 — Utah-Flux 与 m5resolver

**对象：** 软件开发人员  
**前提：** Python 3.10+，可选 PlatformIO

## 1. 安装与启动

```bash
cd host
pip install -e .
```

终端用户双击 `Start Utah Flux Studio.bat`。开发者也可：

```bash
utah-flux-studio
```

## 2. 编译流水线

1. GUI 中搭建积木与连线
2. `POST /api/compile` → `utah_flux.compiler.compile_project`
3. 输出 `intent`（下发设备）与 `wires`（遥测联动）
4. 必须通过 validation、safety、simulation

代码示例：

```python
from utah_flux.compiler import compile_project
from utah_flux.templates import get_template

result = compile_project(get_template("tilt_alarm"))
assert result["ok"]
```

## 3. 项目格式 `.flux.json`

含 `bricks`（积木列表）与 `links`（连线 from/to）。

## 4. 意图协议

见 `schemas/intent.schema.json`。  
串口 115200，每行一个 JSON。

## 5. 可选：串口控制器

```python
from m5resolver import IntentController

ctl = IntentController(port="COM3", registry_path="registry/units.json", enable_agent=True)
ctl.open()
ctl.send_intent({"capability_query": True})
ctl.close()
```

## 6. 添加自定义积木

1. `host/utah_flux/bricks.py`
2. `host/utah_flux/compiler.py`
3. 重启 Studio

## 7. 测试

```bash
pytest
```

## 8. 架构文档

ADR 0001、0003、0004
