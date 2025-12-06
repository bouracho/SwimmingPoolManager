"""Select entity allowing to change pool mode from UI."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import async_get_current_platform
from .const import MODES, DOMAIN

LOGGER = logging.getLogger(__name__)

async def async_setup_select(hass, entry, controller):
    platform = async_get_current_platform()
    entity = ModeSelect(controller, entry.entry_id)
    platform.add_entities([entity])
    LOGGER.debug("Select entity created for entry %s", entry.entry_id)

class ModeSelect(SelectEntity):
    def __init__(self, controller, entry_id):
        self._controller = controller
        self._entry_id = entry_id
        self._attr_name = f"Piscine Mode {entry_id}"
        self._attr_options = MODES
        self._attr_current_option = controller.mode

    @property
    def unique_id(self):
        return f"piscine_mode_{self._entry_id}"

    async def async_select_option(self, option: str):
        LOGGER.info("ModeSelect(%s) set option %s", self._entry_id, option)
        await self._controller.async_set_mode(option)
        self._attr_current_option = option
        self.async_write_ha_state()
