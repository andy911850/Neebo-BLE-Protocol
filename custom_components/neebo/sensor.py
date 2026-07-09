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
        NeeboActivitySensor(hub, entry.entry_id),
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
        val = self._hub.data.get(self._key)
        if val == 0 and self._key in ["hr", "spo2", "temp"]:
            return None
        return val

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

class NeeboActivitySensor(NeeboBaseSensor):
    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id, "activity_state", "Activity State")
        self._attr_icon = "mdi:human-child"
        
    @property
    def state(self):
        val = self._hub.data.get(self._key)
        if val is None:
            return None
        # Try to map common states, or return raw number
        if val == 0:
            return "Asleep"
        elif val == 1:
            return "Awake"
        elif val == 2:
            return "Active"
        else:
            return f"State {val}"
