import asyncio
import struct
import time
from bleak import BleakClient
import logging

_LOGGER = logging.getLogger(__name__)

from .const import (
    CHAR_VITALS, CHAR_BATTERY, CHAR_PLACEMENT, CHAR_ACTIVITY, 
    CHAR_POWER, CHAR_TIME, CMD_WAKE, CMD_STANDBY, CMD_POWER_OFF
)

class NeeboDevice:
    def __init__(self, mac_address):
        self.mac = mac_address
        self.client = None
        self._callbacks = []
        self._loop = asyncio.get_event_loop()
        self._reconnect_task = None
        self._should_run = True
        
        self.data = {
            "hr": None,
            "spo2": None,
            "temp": None,
            "battery": None,
            "on_wrist": None,
            "activity_state": None,
            "standby": False
        }

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def _fire_callbacks(self):
        for cb in self._callbacks:
            self._loop.call_soon_threadsafe(cb)

    def _notification_handler(self, sender, data):
        uuid = str(sender).lower()
        if uuid.startswith(CHAR_VITALS.split('-')[0]):
            if len(data) >= 9:
                hr_val, ox_val, temp_val = struct.unpack_from('<HHH', data, 3)
                self.data["hr"] = hr_val
                self.data["spo2"] = ox_val
                self.data["temp"] = temp_val / 10.0
                self._fire_callbacks()
                
        elif uuid.startswith(CHAR_BATTERY.split('-')[0]):
            if len(data) >= 1:
                self.data["battery"] = data[0]
                self._fire_callbacks()
                
        elif uuid.startswith(CHAR_PLACEMENT.split('-')[0]):
            if len(data) >= 1:
                self.data["on_wrist"] = (data[0] == 2)
                self._fire_callbacks()
                
        elif uuid.startswith(CHAR_ACTIVITY.split('-')[0]):
            if len(data) >= 2:
                val = struct.unpack_from('<H', data, 0)[0]
                self.data["activity_state"] = (val & 0xF000) >> 12
                self._fire_callbacks()

    async def connect(self):
        self._should_run = True
        success = await self._do_connect()
        # Start the background task to keep connection alive
        self._reconnect_task = asyncio.create_task(self._maintain_connection())
        return success

    async def _do_connect(self):
        self.client = BleakClient(self.mac, disconnected_callback=self._on_disconnect)
        try:
            await self.client.connect()
            # Sync time to ensure device functions properly
            timestamp = int(time.time())
            time_bytes = struct.pack('<I', timestamp)
            await self.client.write_gatt_char(CHAR_TIME, time_bytes)
            
            # Subscribe to notifications
            for char in [CHAR_VITALS, CHAR_BATTERY, CHAR_PLACEMENT, CHAR_ACTIVITY]:
                await self.client.start_notify(char, self._notification_handler)
                
            _LOGGER.info(f"Successfully connected and subscribed to Neebo {self.mac}")
            return True
        except Exception as e:
            _LOGGER.error(f"Error connecting to Neebo: {e}")
            return False

    def _on_disconnect(self, client):
        _LOGGER.warning("Neebo disconnected. Background task will reconnect...")

    async def _maintain_connection(self):
        while self._should_run:
            if not self.client or not self.client.is_connected:
                _LOGGER.info("Attempting to reconnect to Neebo...")
                await self._do_connect()
            await asyncio.sleep(10)

    async def disconnect(self):
        self._should_run = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def set_standby(self, enabled: bool):
        if not self.client or not self.client.is_connected:
            return
        cmd = CMD_STANDBY if enabled else CMD_WAKE
        await self.client.write_gatt_char(CHAR_POWER, cmd, response=False)
        self.data["standby"] = enabled
        self._fire_callbacks()

    async def power_off(self):
        if not self.client or not self.client.is_connected:
            return
        await self.client.write_gatt_char(CHAR_POWER, CMD_POWER_OFF, response=False)
