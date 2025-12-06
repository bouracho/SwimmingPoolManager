"""Select entity for pivot hour (15-minute steps)."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import async_get_current_platform
from datetime import time

LOGGER = logging.getLogger(__name__)

def _generate_times():
    opts = []
    for h in range(24):
        for m in range(0,60,15):
            opts.append(f"{h:02d}:{m:02d}")
    return opts

TIME_OPTIONS = _generate_times()

async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    entity = PivotSelect(controller, entry.entry_id)
    async_add_entities([entity])

class PivotSelect(SelectEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._entry_id = entry_id
        self._attr_name = f"Pool Pivot Hour {entry_id}"
        self._attr_unique_id = f"{entry_id}_pivot_select"
        self._attr_options = TIME_OPTIONS
        self._attr_current_option = controller.config.get('pivot_hour')

    async def async_select_option(self, option: str):
        LOGGER.info("PivotSelect set %s", option)
        self.controller.update_config('pivot_hour', option)
        self._attr_current_option = option
        self.async_write_ha_state()