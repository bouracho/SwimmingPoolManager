from homeassistant.components.select import SelectEntity
from .const import DOMAIN, MODES

async def async_setup_select(hass, entry, controller):
    entity = ModeSelect(controller, entry.entry_id)
    hass.helpers.entity_platform.async_get_current_platform().add_entities([entity])

class ModeSelect(SelectEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Piscine Mode {entry_id}"
        self._attr_options = MODES
        self._attr_current_option = controller.mode

    async def async_select_option(self, option):
        if option in MODES:
            self.controller.mode = option
            self._attr_current_option = option
            self.async_write_ha_state()