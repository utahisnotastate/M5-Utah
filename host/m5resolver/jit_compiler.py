from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("m5resolver.jit")

MAX_JIT_CODE_BYTES = 4096
MIN_JIT_CODE_BYTES = 4


def verify_iram_payload_safe(size_in_bytes: int, *, limit: int = MAX_JIT_CODE_BYTES) -> bool:
    """Gatekeeper for IRAM injection size (matches firmware RuntimeLinker::kMaxCodeBytes)."""
    return MIN_JIT_CODE_BYTES <= size_in_bytes <= limit


class HostJitCompiler:
    """
    Host-side micro-compilation pipeline for position-independent Xtensa payloads.

    Requires xtensa-esp32-elf-gcc / objcopy on PATH when compiling C sources.
    """

    def __init__(
        self,
        toolchain_prefix: str = "xtensa-esp32-elf",
        *,
        mcu_flags: list[str] | None = None,
    ) -> None:
        self.compiler = f"{toolchain_prefix}-gcc"
        self.objcopy = f"{toolchain_prefix}-objcopy"
        self.mcu_flags = mcu_flags or ["-mlongcalls"]

    def toolchain_available(self) -> bool:
        return shutil.which(self.compiler) is not None and shutil.which(self.objcopy) is not None

    def compile_logic_to_raw_bytes(
        self,
        c_code_string: str,
        *,
        output_bin_path: str | Path | None = None,
        work_dir: str | Path | None = None,
    ) -> bytes | None:
        if not self.toolchain_available():
            logger.error("JIT toolchain not found: %s", self.compiler)
            return None

        cleanup_dir = False
        if work_dir is None:
            work_dir = tempfile.mkdtemp(prefix="m5utah-jit-")
            cleanup_dir = True
        work = Path(work_dir)
        work.mkdir(parents=True, exist_ok=True)

        source_temp = work / "temp_vibe.c"
        obj_temp = work / "temp_vibe.o"
        bin_path = Path(output_bin_path) if output_bin_path else work / "output.bin"

        source = self._wrap_source(c_code_string)
        source_temp.write_text(source, encoding="utf-8")

        try:
            compile_cmd = [
                self.compiler,
                "-c",
                str(source_temp),
                "-o",
                str(obj_temp),
                "-fPIC",
                "-O3",
                "-nostdlib",
                "-fno-builtin",
                *self.mcu_flags,
            ]
            logger.info("[JIT] Emitting compilation command sequence...")
            subprocess.run(compile_cmd, check=True, capture_output=True, text=True)

            extract_cmd = [
                self.objcopy,
                "-O",
                "binary",
                "--only-section=.text",
                str(obj_temp),
                str(bin_path),
            ]
            subprocess.run(extract_cmd, check=True, capture_output=True, text=True)

            raw_machine_bytes = bin_path.read_bytes()
            if len(raw_machine_bytes) > MAX_JIT_CODE_BYTES:
                logger.error(
                    "Compiled payload exceeds IRAM safe limit (%s > %s bytes)",
                    len(raw_machine_bytes),
                    MAX_JIT_CODE_BYTES,
                )
                return None
            if len(raw_machine_bytes) < MIN_JIT_CODE_BYTES:
                logger.error("Compiled payload too small for safe execution.")
                return None

            logger.info(
                "[SUCCESS] Native assembly package compiled successfully: %s bytes.",
                len(raw_machine_bytes),
            )
            return raw_machine_bytes
        except subprocess.CalledProcessError as exc:
            logger.error("Compilation pipeline failed: %s", exc.stderr or exc)
            return None
        finally:
            for temp_file in (source_temp, obj_temp, bin_path):
                if temp_file.exists():
                    temp_file.unlink(missing_ok=True)
            if cleanup_dir:
                shutil.rmtree(work, ignore_errors=True)

    def compile_intent_to_assembly(self, c_code_payload: str) -> bytes | None:
        """Alias for vibe-coded C snippets → position-independent .text bytes."""
        return self.compile_logic_to_raw_bytes(c_code_payload)

    @staticmethod
    def _wrap_source(c_code_string: str) -> str:
        stripped = c_code_string.strip()
        if "vDynamicTask" in stripped or stripped.startswith("void"):
            return stripped if stripped.endswith("\n") else stripped + "\n"
        return f"void vDynamicTask(void) {{\n{stripped}\n}}\n"

    @staticmethod
    def pack_jit_intent(
        machine_bytes: bytes,
        *,
        unit_id: str = "custom_asm_routine",
        execute: bool = True,
    ) -> dict[str, Any]:
        if len(machine_bytes) > MAX_JIT_CODE_BYTES:
            raise ValueError(f"JIT payload exceeds {MAX_JIT_CODE_BYTES} byte limit")
        return {
            "native_jit": {
                "unit_id": unit_id,
                "type": "native_jit_patch",
                "code_size_bytes": len(machine_bytes),
                "payload_hex": machine_bytes.hex(),
                "execute": execute,
            }
        }


def validate_native_jit_block(block: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if block.get("type") != "native_jit_patch":
        errors.append("native_jit.type must be native_jit_patch")

    code_size = block.get("code_size_bytes")
    payload_hex = block.get("payload_hex")

    if not isinstance(payload_hex, str) or not payload_hex:
        errors.append("native_jit.payload_hex is required")
        return errors

    if len(payload_hex) % 2 != 0:
        errors.append("native_jit.payload_hex must have even length")

    try:
        decoded = bytes.fromhex(payload_hex)
    except ValueError:
        errors.append("native_jit.payload_hex must be valid hexadecimal")
        return errors

    if len(decoded) > MAX_JIT_CODE_BYTES:
        errors.append(
            f"native_jit payload exceeds safe IRAM limit ({MAX_JIT_CODE_BYTES} bytes)"
        )
    if len(decoded) < MIN_JIT_CODE_BYTES:
        errors.append("native_jit payload too small for execution")

    if code_size is not None:
        if not isinstance(code_size, int):
            errors.append("native_jit.code_size_bytes must be an integer")
        elif code_size != len(decoded):
            errors.append("native_jit.code_size_bytes does not match payload_hex length")

    if "execute" in block and not isinstance(block["execute"], bool):
        errors.append("native_jit.execute must be a boolean")

    return errors


def validate_jit_units(units: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for unit_id, cfg in units.items():
        if not isinstance(cfg, dict):
            continue
        if cfg.get("type") != "native_jit_patch":
            continue
        block_errors = validate_native_jit_block({"unit_id": unit_id, **cfg})
        errors.extend(block_errors)
    return errors
