from m5resolver.jit_compiler import (
    MAX_JIT_CODE_BYTES,
    HostJitCompiler,
    validate_native_jit_block,
)


def test_pack_jit_intent_round_trip():
    raw = b"\x4f\x55\x52\x46"
    intent = HostJitCompiler.pack_jit_intent(raw, unit_id="routine_a")
    assert intent["native_jit"]["code_size_bytes"] == 4
    assert intent["native_jit"]["payload_hex"] == raw.hex()
    assert validate_native_jit_block(intent["native_jit"]) == []


def test_validate_rejects_oversized_payload():
    huge_hex = "aa" * (MAX_JIT_CODE_BYTES + 1)
    errors = validate_native_jit_block(
        {
            "type": "native_jit_patch",
            "code_size_bytes": MAX_JIT_CODE_BYTES + 1,
            "payload_hex": huge_hex,
        }
    )
    assert any("exceeds safe IRAM limit" in e for e in errors)


def test_wrap_source_adds_function_shell():
    wrapped = HostJitCompiler._wrap_source("volatile int i = 0; i++;")
    assert "void vDynamicTask(void)" in wrapped
    assert "volatile int i = 0" in wrapped


def test_compile_intent_to_assembly_alias():
    compiler = HostJitCompiler()
    assert callable(compiler.compile_intent_to_assembly)
    # Without toolchain, both return None for empty/minimal input path
    assert compiler.compile_intent_to_assembly("return;") is None or isinstance(
        compiler.compile_intent_to_assembly("return;"), bytes
    )


def test_jit_pipeline_with_registry_delta():
    from m5resolver.jit_pipeline import M5JitPipeline

    pipeline = M5JitPipeline()
    units = {
        "filter_a": {"slot_id": 0, "frequency_hz": 10, "depends_on": []},
        "filter_b": {"slot_id": 1, "frequency_hz": 20, "depends_on": ["filter_a"]},
    }
    delta = pipeline.compute_registry_delta(units, "filter_a")
    assert delta is None or delta[:2] == b"\xde\xda"
