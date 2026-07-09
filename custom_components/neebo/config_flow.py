import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    async_discovered_service_info,
    async_ble_device_from_address,
)
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from .const import DOMAIN

WIFI_NAME_CHAR = "0000ffb1-0000-1000-8000-00805f9b34fb"
WIFI_PASS_CHAR = "0000ffb2-0000-1000-8000-00805f9b34fb"
MQTT_ADDR_CHAR = "0000ffc1-0000-1000-8000-00805f9b34fb"
MQTT_PASS_CHAR = "0000ffc2-0000-1000-8000-00805f9b34fb"

class NeeboConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.discovered_devices = {}
        self.selected_base_station = None

    async def async_step_user(self, user_input=None):
        return self.async_show_menu(
            step_id="user",
            menu_options=["bluetooth", "base_station"]
        )

    async def async_step_bluetooth(self, user_input=None):
        if user_input is not None:
            mac = user_input["address"]
            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"Neebo Bracelet ({mac})", data={"mac": mac, "mode": "bluetooth"})

        self.discovered_devices = {}
        current_devices = async_discovered_service_info(self.hass)
        for info in current_devices:
            if info.name == "NB0":
                self.discovered_devices[info.address] = f"Neebo Bracelet ({info.address})"

        if not self.discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema({
            vol.Required("address"): vol.In(self.discovered_devices)
        })

        return self.async_show_form(
            step_id="bluetooth",
            data_schema=data_schema
        )

    async def async_step_base_station(self, user_input=None):
        if user_input is not None:
            self.selected_base_station = user_input["address"]
            return await self.async_step_base_station_wifi()

        self.discovered_devices = {}
        current_devices = async_discovered_service_info(self.hass)
        for info in current_devices:
            if info.name == "NC0":
                self.discovered_devices[info.address] = f"Base Station ({info.address})"

        if not self.discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema({
            vol.Required("address"): vol.In(self.discovered_devices)
        })

        return self.async_show_form(
            step_id="base_station",
            data_schema=data_schema
        )

    async def async_step_base_station_wifi(self, user_input=None):
        errors = {}
        if user_input is not None:
            wifi_ssid = user_input["wifi_ssid"]
            wifi_pass = user_input.get("wifi_pass", "")
            mqtt_addr = user_input["mqtt_addr"]
            mqtt_pass = user_input.get("mqtt_pass", "")
            serial_num = user_input["serial_number"].upper()

            ble_device = async_ble_device_from_address(self.hass, self.selected_base_station, connectable=True)
            if ble_device:
                try:
                    client = await establish_connection(
                        client_class=BleakClientWithServiceCache,
                        device=ble_device,
                        name=ble_device.name
                    )
                    try:
                        if wifi_ssid:
                            await client.write_gatt_char(WIFI_NAME_CHAR, wifi_ssid.encode('utf-8'))
                        if wifi_pass:
                            await client.write_gatt_char(WIFI_PASS_CHAR, wifi_pass.encode('utf-8'))
                        if mqtt_addr:
                            await client.write_gatt_char(MQTT_ADDR_CHAR, mqtt_addr.encode('utf-8'))
                        if mqtt_pass:
                            await client.write_gatt_char(MQTT_PASS_CHAR, mqtt_pass.encode('utf-8'))
                    finally:
                        await client.disconnect()
                            
                            
                    await self.async_set_unique_id(serial_num)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Neebo Base Station ({serial_num})", 
                        data={"serial_number": serial_num, "mode": "mqtt"}
                    )
                except Exception as e:
                    errors["base"] = "cannot_connect"
            else:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema({
            vol.Required("serial_number"): str,
            vol.Required("wifi_ssid"): str,
            vol.Optional("wifi_pass"): str,
            vol.Required("mqtt_addr"): str,
            vol.Optional("mqtt_pass"): str,
        })

        return self.async_show_form(
            step_id="base_station_wifi",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"instructions": "IMPORTANT: You MUST add your Serial Number as a Mosquitto user first!"}
        )
