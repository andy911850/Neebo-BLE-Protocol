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
            cb()

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
                
            return True
        except Exception as e:
            _LOGGER.error(f"Error connecting to Neebo: {e}")
            return False

    def _on_disconnect(self, client):
        _LOGGER.warning("Neebo disconnected")
        # In a real integration, we'd trigger a reconnect loop here

    async def disconnect(self):
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

import json
from homeassistant.components import mqtt

class NeeboMqttDevice:
    def __init__(self, hass, serial_number):
        self.hass = hass
        self.serial = serial_number
        self.mac = serial_number  # For compatibility with existing sensors
        self._callbacks = []
        self._unsub = None
        
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
            cb()

    async def connect(self):
        topic = f"/nbo_charger/v1.0/{self.serial}/get/advertising"
        
        async def message_received(msg):
            try:
                payload = json.loads(msg.payload)
                if "vitals" in payload:
                    self.data["hr"] = payload["vitals"][0]["hr"]["value"]
                    self.data["spo2"] = payload["vitals"][1]["ox"]["value"]
                    
                    # Convert temperature if provided. BLE is in tenths, so we assume JSON is too based on our mapping, 
                    # but maybe JSON is already float? No, JSON showed 0. We'll divide by 10 for consistency.
                    temp_val = payload["vitals"][2]["temp"]["value"]
                    self.data["temp"] = temp_val / 10.0 if temp_val > 0 else 0
                    
                if "battery" in payload:
                    self.data["battery"] = payload["battery"]
                if "placement" in payload:
                    self.data["on_wrist"] = (payload["placement"] == 2)
                if "activity_state" in payload:
                    self.data["activity_state"] = payload["activity_state"]
                if "standby" in payload:
                    self.data["standby"] = (payload["standby"] == 1)
                    
                self._fire_callbacks()
            except Exception as e:
                _LOGGER.error(f"Error parsing MQTT payload: {e}")
                
        self._unsub = await mqtt.async_subscribe(self.hass, topic, message_received)
        return True

    async def disconnect(self):
        if self._unsub:
            self._unsub()
            
    async def set_standby(self, enabled: bool):
        pass

    async def power_off(self):
        pass
