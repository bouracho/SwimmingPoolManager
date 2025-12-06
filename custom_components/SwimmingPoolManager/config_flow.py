"""Config flow for Pool Manager."""
from __future__ import annotations
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
from .const import DOMAIN, CONF_WATER_TEMP, CONF_PUMP_SWITCH, CONF_PIVOT_HOUR, CONF_PAUSE_MINUTES, CONF_CUT_DURATION_MIN, CONF_ANTI_FREEZE_TEMP, CONF_ROBOT_ENABLED, CONF_ROBOT_SWITCH, CONF_ADJUST_COEFF, CONF_OUTDOOR_TEMP, CONF_NO_FROST_TEMP

LOGGER = logging.getLogger(__name__)

class PoolManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            LOGGER.debug("config_flow user input: %s", user_input)
            self._data.update(user_input)
            # If robot enabled, robot switch may be provided or asked in next step
            return self.async_create_entry(title="Swimming Pool Manager", data=self._data)

        schema = vol.Schema({
            vol.Required(CONF_WATER_TEMP): EntitySelector(EntitySelectorConfig(domain=["sensor"])),
            vol.Required(CONF_PUMP_SWITCH): EntitySelector(EntitySelectorConfig(domain=["switch"])),
            vol.Required(CONF_OUTDOOR_TEMP): EntitySelector(EntitySelectorConfig(domain=["sensor"])),
            vol.Required(CONF_PIVOT_HOUR): str,
            vol.Required(CONF_PAUSE_MINUTES, default=0): int,
            vol.Required(CONF_CUT_DURATION_MIN, default=60): int,
            vol.Required(CONF_ANTI_FREEZE_TEMP, default=2.0): float,
            vol.Optional(CONF_ROBOT_ENABLED, default=False): bool,
            vol.Optional(CONF_ROBOT_SWITCH): EntitySelector(EntitySelectorConfig(domain=["switch"])),
            vol.Optional(CONF_ADJUST_COEFF, default=100): vol.All(int, vol.Range(min=10, max=100)),
            vol.Required(CONF_NO_FROST_TEMP, default=0.0): float,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
