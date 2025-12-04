import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
from .const import DOMAIN, CONF_WATER_TEMP, CONF_PUMP_SWITCH, CONF_PIVOT_TIME, CONF_CUT_DURATION, CONF_ANTI_FREEZE_TEMP, CONF_BREAK_DURATION
import logging
LOGGER = logging.getLogger(__name__)

class PiscineManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            self._data = user_input
            if user_input.get("robot_enabled", False):
                return await self.async_step_robot()
            return self.async_create_entry(title="Piscine", data=self._data)

        schema = vol.Schema({
            vol.Required(CONF_WATER_TEMP): EntitySelector(EntitySelectorConfig(domain=["sensor"])),
            vol.Required(CONF_PUMP_SWITCH): EntitySelector(EntitySelectorConfig(domain=["switch"])),
            vol.Required(CONF_PIVOT_TIME): str,
            vol.Required(CONF_CUT_DURATION, default=60): int,
            vol.Required(CONF_BREAK_DURATION, default=0): int,
            vol.Required(CONF_ANTI_FREEZE_TEMP): float,
            vol.Optional("robot_enabled", default=False): bool
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_robot(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._data["robot_switch"] = user_input.get("robot_switch")
            self._data["robot_enabled"] = True
            return self.async_create_entry(title="Piscine", data=self._data)

        schema = vol.Schema({
            vol.Required("robot_switch"): EntitySelector(EntitySelectorConfig(domain=["switch"]))
        })

        return self.async_show_form(step_id="robot", data_schema=schema, errors=errors)
