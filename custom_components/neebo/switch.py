from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NeeboStandbySwitch(hub, entry.entry_id)])

class NeeboStandbySwitch(SwitchEntity):
    def __init__(self, hub, entry_id):
        self._hub = hub
        self._attr_name = "Neebo Standby Mode"
        self._attr_unique_id = f"{entry_id}_standby"
        self._attr_icon = "mdi:power-sleep"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Neebo Monitor",
            manufacturer="Daatrics Ltd",
        )

    @property
    def is_on(self):
        return self._hub.data.get("standby", False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on (put device in standby)."""
        await self._hub.set_standby(True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off (wake device up)."""
        await self._hub.set_standby(False)

    async def async_added_to_hass(self):
        self._hub.register_callback(self.async_write_ha_state)
