from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .hub import NeeboDevice, NeeboMqttDevice
import asyncio
PLATFORMS = ["sensor", "binary_sensor", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    mode = entry.data.get("mode", "bluetooth")
    if mode == "mqtt":
        serial = entry.data["serial_number"]
        hub = NeeboMqttDevice(hass, serial)
    else:
        mac = entry.data["mac"]
        hub = NeeboDevice(mac)
    
    connected = await hub.connect()
    if not connected:
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.disconnect()
    return unload_ok
