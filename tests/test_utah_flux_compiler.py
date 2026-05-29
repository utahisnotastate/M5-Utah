from utah_flux.compiler import compile_project
from utah_flux.templates import get_template


def test_compile_hello_template():
    project = get_template("hello")
    assert project is not None
    result = compile_project(project)
    assert result["ok"] is True
    assert "display" in result["intent"]


def test_compile_tilt_template_has_wires():
    project = get_template("tilt_alarm")
    assert project is not None
    result = compile_project(project)
    assert result["ok"] is True
    assert len(result["wires"]) >= 1
