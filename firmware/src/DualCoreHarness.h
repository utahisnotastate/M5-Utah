#pragma once

#include "BinwireDecoder.h"
#include "CrossCorePipe.h"
#include "M5Kernel.h"

#include <freertos/ringbuf.h>
#include <stdint.h>

/**
 * SOTA Feature 52 — Dual-Core Non-Blocking Execution Harness
 *
 * Core 0 (protocol engine): serial demux, ## fast-path intercept, ring push (non-blocking).
 * Core 1 (application engine): ring drain, hardware dispatch, no blocking Serial I/O.
 *
 * Implemented by CrossCorePipe + M5Kernel; this header documents the wire/memory contract.
 */

constexpr int kDualCoreProtocolEngine = kM5KernelCoreProtocol;
constexpr int kDualCoreApplicationEngine = kM5KernelCoreApplication;

constexpr size_t kFastPathQueueMinBytes = 512;
constexpr size_t kFastPathQueueBytes = kCrossCoreRingBytes;

/** Packed ## binwire layout pushed through the cross-core ring as kPipeFrameBinary. */
using DirectHardwareCommand = BinwireCommand;

static_assert(sizeof(DirectHardwareCommand) == 8, "DirectHardwareCommand must match !BBHI wire layout");

inline RingbufHandle_t dualCoreFastPathQueueHandle() {
  return globalCorePipe().isReady() ? globalCorePipe().nativeHandle() : nullptr;
}
