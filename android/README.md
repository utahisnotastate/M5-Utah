# m5-utah Android Companion

Zero-driver USB Host integration for M5Stack and ESP32 CDC-ACM devices.

## Modules

| Path | Purpose |
|------|---------|
| `transport/FastPathUsbBridge.kt` | USB bulk OUT binwire/RPP frames |
| `transport/WireFrames.kt` | Big-endian `##` and `#P` packers (10 bytes) |
| `mesh/FluxwireMeshNode.kt` | UDP gossip mesh node (`android_host_node`) |
| `mesh/MeshRegistryMirror.kt` | Local in-memory `units.json` mirror |
| `mesh/AndroidMeshParticipant.kt` | Gossip → audit → USB binwire routing |

## Wire contract

Binwire frames must match firmware `DirectHardwareCommand` / host `BinwireEncoder`:

```
[0x23, 0x23] + unit_id(u8) + pin(u8) + frequency_hz(u16 BE) + state_mask(u32 BE)
```

Python contract tests live in `tests/test_fluxwire.py` (`test_android_payload_binary_signature`).

## Usage sketch

```kotlin
val bridge = FastPathUsbBridge(usbManager)
bridge.initializeHardwareConnection(device)
bridge.onTelemetryLine = { line -> Log.d("m5", line) }
bridge.dispatchFastPathIntent(
    unitId = 7,
    pinTarget = 10,
    frequencyHz = 50,
    stateMask = 412,
)
```

## Host parity

`host/m5resolver/android_bridge.py` mirrors the Kotlin packers for CI validation.

## Fluxwire mesh

`FluxwireMeshNode` listens on UDP **23023**, matching `FluxwireGossipMesh` in the Python host.

`AndroidMeshParticipant` combines gossip ingestion, `MeshRegistryMirror`, pre-flight audit,
and `FastPathUsbBridge` dispatch — use when the companion app should react to mesh
registry updates without a desktop host:

```kotlin
val participant = AndroidMeshParticipant(usbBridge)
participant.start()
participant.publishLocalRegistry(localUnitsJson)
```
