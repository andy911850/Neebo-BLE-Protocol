import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, async_discovered_service_info
from .const import DOMAIN

class NeeboConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.discovered_devices = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            mac = user_input["address"]
            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"Neebo ({mac})", data={"mac": mac})

        # Discover nearby Neebo devices (NB0)
        current_devices = async_discovered_service_info(self.hass)
        for info in current_devices:
            if info.name == "NB0":
                self.discovered_devices[info.address] = f"Neebo Monitor ({info.address})"

        if not self.discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema({
            vol.Required("address"): vol.In(self.discovered_devices)
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            description_placeholders={"instructions": "Select your Neebo monitor from the list."},
        )
