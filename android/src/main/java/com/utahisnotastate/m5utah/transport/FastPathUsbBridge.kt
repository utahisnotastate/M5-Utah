package com.utahisnotastate.m5utah.transport

import android.hardware.usb.UsbConstants
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbDeviceConnection
import android.hardware.usb.UsbEndpoint
import android.hardware.usb.UsbInterface
import android.hardware.usb.UsbManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.nio.charset.Charset

/**
 * Zero-driver USB Host serial bridge for M5Stack / ESP32 CDC-ACM devices.
 *
 * Packs UI gestures into fixed-width binwire (##) or RPP (#P) frames matching
 * firmware CrossCorePipe demux on Core 0.
 */
class FastPathUsbBridge(
    private val usbManager: UsbManager,
    private val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO),
) {
    private var connection: UsbDeviceConnection? = null
    private var writeEndpoint: UsbEndpoint? = null
    private var readEndpoint: UsbEndpoint? = null
    private var claimedInterface: UsbInterface? = null

    var onTelemetryLine: ((String) -> Unit)? = null

    fun initializeHardwareConnection(device: UsbDevice): Boolean {
        release()

        for (index in 0 until device.interfaceCount) {
            val usbInterface = device.getInterface(index)
            var bulkOut: UsbEndpoint? = null
            var bulkIn: UsbEndpoint? = null

            for (endpointIndex in 0 until usbInterface.endpointCount) {
                val endpoint = usbInterface.getEndpoint(endpointIndex)
                if (endpoint.type != UsbConstants.USB_ENDPOINT_XFER_BULK) continue
                if (endpoint.direction == UsbConstants.USB_DIR_OUT) {
                    bulkOut = endpoint
                } else if (endpoint.direction == UsbConstants.USB_DIR_IN) {
                    bulkIn = endpoint
                }
            }

            if (bulkOut == null) continue

            val devConnection = usbManager.openDevice(device) ?: continue
            if (!devConnection.claimInterface(usbInterface, true)) {
                devConnection.close()
                continue
            }

            connection = devConnection
            claimedInterface = usbInterface
            writeEndpoint = bulkOut
            readEndpoint = bulkIn
            startTelemetryReader()
            return true
        }
        return false
    }

    /**
     * Non-allocating mobile-to-silicon binwire dispatch (## magic, !BBHI layout).
     */
    fun dispatchFastPathIntent(
        unitId: Byte,
        pinTarget: Byte,
        frequencyHz: Short,
        stateMask: Int,
        timeoutMs: Int = 100,
    ) {
        val frame = BinwireFrame.pack(unitId, pinTarget, frequencyHz, stateMask)
        bulkWrite(frame, timeoutMs)
    }

    /** Asymmetric RPP (#P) remote procedure frame. */
    fun dispatchRppIntent(
        unitId: Byte,
        opcode: Byte,
        dataVector: Short,
        sequenceId: Int,
        timeoutMs: Int = 100,
    ) {
        val frame = RppFrame.pack(unitId, opcode, dataVector, sequenceId)
        bulkWrite(frame, timeoutMs)
    }

    fun dispatchRawFrame(frame: ByteArray, timeoutMs: Int = 100) {
        bulkWrite(frame, timeoutMs)
    }

    private fun bulkWrite(rawBytes: ByteArray, timeoutMs: Int) {
        scope.launch {
            val devConnection = connection ?: return@launch
            val endpoint = writeEndpoint ?: return@launch
            devConnection.bulkTransfer(endpoint, rawBytes, rawBytes.size, timeoutMs)
        }
    }

    private fun startTelemetryReader() {
        val devConnection = connection ?: return
        val endpoint = readEndpoint ?: return

        scope.launch {
            val buffer = ByteArray(512)
            val charset = Charset.forName("UTF-8")
            while (connection != null) {
                val read = devConnection.bulkTransfer(endpoint, buffer, buffer.size, 200)
                if (read > 0) {
                    val line = charset.decode(buffer.copyOf(read))
                    onTelemetryLine?.invoke(line.trim())
                }
            }
        }
    }

    fun release() {
        connection?.let { conn ->
            claimedInterface?.let { iface -> conn.releaseInterface(iface) }
            conn.close()
        }
        connection = null
        writeEndpoint = null
        readEndpoint = null
        claimedInterface = null
    }
}
