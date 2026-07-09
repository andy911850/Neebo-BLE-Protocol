from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NeeboPlacementSensor(hub, entry.entry_id)])

class NeeboPlacementSensor(BinarySensorEntity):
    def __init__(self, hub, entry_id):
        self._hub = hub
        self._attr_name = "Neebo On Wrist"
        self._attr_unique_id = f"{entry_id}_placement"
        self._attr_device_class = BinarySensorDeviceClass.PRESENCE
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Neebo Monitor",
            manufacturer="Daatrics Ltd",
        )

    @property
    def is_on(self):
        return self._hub.data.get("on_wrist", False)

    async def async_added_to_hass(self):
        self._hub.register_callback(self.async_write_ha_state)
