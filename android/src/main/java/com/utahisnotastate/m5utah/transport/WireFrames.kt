package com.utahisnotastate.m5utah.transport

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Fixed-width wire contracts shared with firmware BinwireDecoder / DirectHardwareCommand.
 * Must stay byte-identical to host/m5resolver/binwire.py and FastPathUsbBridge.
 */
object BinwireFrame {
    const val FRAME_LEN: Int = 10
    const val MAGIC_0: Byte = 0x23
    const val MAGIC_1: Byte = 0x23

    fun pack(
        unitId: Byte,
        pinTarget: Byte,
        frequencyHz: Short,
        stateMask: Int,
    ): ByteArray {
        return ByteBuffer.allocate(FRAME_LEN).apply {
            order(ByteOrder.BIG_ENDIAN)
            put(MAGIC_0)
            put(MAGIC_1)
            put(unitId)
            put(pinTarget)
            putShort(frequencyHz)
            putInt(stateMask)
        }.array()
    }
}

object RppFrame {
    const val FRAME_LEN: Int = 10
    const val MAGIC_0: Byte = 0x23
    const val MAGIC_1: Byte = 0x50

    fun pack(
        unitId: Byte,
        opcode: Byte,
        dataVector: Short,
        sequenceId: Int,
    ): ByteArray {
        return ByteBuffer.allocate(FRAME_LEN).apply {
            order(ByteOrder.BIG_ENDIAN)
            put(MAGIC_0)
            put(MAGIC_1)
            put(unitId)
            put(opcode)
            putShort(dataVector)
            putInt(sequenceId)
        }.array()
    }
}
