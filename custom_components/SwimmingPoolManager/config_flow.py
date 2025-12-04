"""Config flow for Piscine Manager."""
from __future__ import annotations
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
from .const import DOMAIN, CONF_WATER_TEMP, CONF_PUMP_SWITCH, CONF_PIVOT_TIME, CONF_CUT_DURATION, CONF_BREAK_DURATION, CONF_ANTI_FREEZE_TEMP, CONF_ROBOT_ENABLED, CONF_ROBOT_SWITCH

LOGGER = logging.getLogger(__name__)

class PiscineManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            LOGGER.debug("config_flow: user input %s", user_input)
            self._data.update(user_input)
            if user_input.get(CONF_ROBOT_ENABLED, False):
                return await self.async_step_robot()
            return self.async_create_entry(title="Piscine", data=self._data)

        schema = vol.Schema({
            vol.Required(CONF_WATER_TEMP): EntitySelector(EntitySelectorConfig(domain=["sensor"])),
            vol.Required(CONF_PUMP_SWITCH): EntitySelector(EntitySelectorConfig(domain=["switch"])),
            vol.Required(CONF_PIVOT_TIME): str,
            vol.Required(CONF_CUT_DURATION, default=60): int,
            vol.Required(CONF_BREAK_DURATION, default=0): int,
            vol.Required(CONF_ANTI_FREEZE_TEMP, default=2.0): float,
            vol.Optional(CONF_ROBOT_ENABLED, default=False): bool,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_robot(self, user_input=None):
        errors = {}
        if user_input is not None:
            LOGGER.debug("config_flow: robot input %s", user_input)
            self._data[CONF_ROBOT_SWITCH] = user_input.get(CONF_ROBOT_SWITCH)
            self._data[CONF_ROBOT_ENABLED] = True
            return self.async_create_entry(title="Piscine", data=self._data)

        schema = vol.Schema({
            vol.Required(CONF_ROBOT_SWITCH): EntitySelector(EntitySelectorConfig(domain=["switch"])),
        })

        return self.async_show_form(step_id="robot", data_schema=schema, errors=errors)
