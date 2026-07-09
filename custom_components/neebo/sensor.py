from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        NeeboHeartRateSensor(hub, entry.entry_id),
        NeeboSpO2Sensor(hub, entry.entry_id),
        NeeboTemperatureSensor(hub, entry.entry_id),
        NeeboBatterySensor(hub, entry.entry_id),
    ])

class NeeboBaseSensor(SensorEntity):
    def __init__(self, hub, entry_id, key, name):
        self._hub = hub
        self._key = key
        self._attr_name = f"Neebo {name}"
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Neebo Monitor",
            manufacturer="Daatrics Ltd",
        )

    @property
    def state(self):
        return self._hub.data.get(self._key)

    async def async_added_to_hass(self):
        self._hub.register_callback(self.async_write_ha_state)

class NeeboHeartRateSensor(NeeboBaseSensor):
    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id, "hr", "Heart Rate")
        self._attr_icon = "mdi:heart-pulse"
        self._attr_native_unit_of_measurement = "bpm"
        self._attr_state_class = SensorStateClass.MEASUREMENT

class NeeboSpO2Sensor(NeeboBaseSensor):
    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id, "spo2", "Oxygen Saturation")
        self._attr_icon = "mdi:air-filter"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

class NeeboTemperatureSensor(NeeboBaseSensor):
    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id, "temp", "Temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT

class NeeboBatterySensor(NeeboBaseSensor):
    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id, "battery", "Battery")
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
