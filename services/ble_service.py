# services/ble_service.py
import asyncio
import struct
import time
from bleak import BleakScanner, BleakClient
from utils.constants import BLE_CONFIG

class BLEService:
    def __init__(self):
        self.client = None
        self.connected_device = None

    async def scan(self, timeout=None):
        timeout = timeout or BLE_CONFIG["SCAN_TIMEOUT"]
        devices = await BleakScanner.discover(timeout=timeout)
        filtered = [d for d in devices if any(name in (d.name or "") for name in BLE_CONFIG["DEVICE_NAME_FILTER"])]
        return filtered

    async def connect(self, device):
        if self.client and self.client.is_connected:
            await self.disconnect()
        self.client = BleakClient(device)
        await self.client.connect()
        self.connected_device = device
        return True

    async def start_notify(self, callback):
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Not connected")

        async def _notification_handler(sender, data):
            try:
                # Unpack 5 little-endian floats (20 bytes total)
                # Hardware sends: emaL, eventOn_left, F_L, F_R, eventOn_right
                emaL, eventOn_left, F_L, F_R, eventOn_right = struct.unpack("<fffff", data)
                # Generate timestamp in milliseconds (used for both sensors)
                timestamp_ms = int(time.time() * 1000)

                # Create CSV format: sensorId,force_kg,timestamp,event_flag
                csv_left = f"1,{F_L},{timestamp_ms},{eventOn_left}"

                # Create CSV format: sensorId,force_kg,timestamp,event_flag
                csv_right = f"2,{F_R},{timestamp_ms},{eventOn_right}"

                # Call the provided callback with both CSV strings
                callback(csv_left)
                callback(csv_right)
            except Exception as e:
                print(f"BLE notification handler error: {e}")

        await self.client.start_notify(BLE_CONFIG["CHARACTERISTIC_UUID_TX"], _notification_handler)

    async def calibrate_rest(self):
        """Send rest calibration command to device"""
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Not connected")
        await self.client.write_gatt_char(BLE_CONFIG["CHARACTERISTIC_UUID_TX"], b"r")

    async def calibrate_bite(self):
        """Send bite/max calibration command to device"""
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Not connected")
        await self.client.write_gatt_char(BLE_CONFIG["CHARACTERISTIC_UUID_TX"], b"m")

    async def stop(self):
        if self.client:
            try:
                await self.client.disconnect()
            finally:
                self.client = None
                self.connected_device = None
