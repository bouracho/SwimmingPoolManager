"""Number entities to allow runtime parameter adjustments via UI."""
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity_platform import async_get_current_platform
from .const import CONF_ADJUST_COEFF, CONF_PAUSE_MINUTES, CONF_CUT_DURATION_MIN, CONF_ANTI_FREEZE_TEMP

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    entities = [AdjustCoeffNumber(controller, entry.entry_id), PauseNumber(controller, entry.entry_id), CutDurationNumber(controller, entry.entry_id), AntiFreezeNumber(controller, entry.entry_id)]
    async_add_entities(entities)

class AdjustCoeffNumber(NumberEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Pool Adjust Coeff {entry_id}"
        self._attr_unique_id = f"{entry_id}_adjust_coeff"
        self._attr_native_min_value = 10
        self._attr_native_max_value = 100
        self._attr_native_step = 1

    @property
    def native_value(self):
        return int(self.controller.config.get('adjust_coeff_pct',100))

    async def async_set_native_value(self, value):
        self.controller.update_config('adjust_coeff_pct', int(value))

class PauseNumber(NumberEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Pool Pause Minutes {entry_id}"
        self._attr_unique_id = f"{entry_id}_pause_minutes"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1440
        self._attr_native_step = 1

    @property
    def native_value(self):
        return int(self.controller.config.get('pause_minutes',0))

    async def async_set_native_value(self, value):
        self.controller.update_config('pause_minutes', int(value))

class CutDurationNumber(NumberEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Pool Cut Duration Min {entry_id}"
        self._attr_unique_id = f"{entry_id}_cut_minutes"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 1440
        self._attr_native_step = 1

    @property
    def native_value(self):
        return int(self.controller.config.get('cut_duration_minutes',60))

    async def async_set_native_value(self, value):
        self.controller.update_config('cut_duration_minutes', int(value))

class AntiFreezeNumber(NumberEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Pool No Frost Temp {entry_id}"
        self._attr_unique_id = f"{entry_id}_nofrost_temp"
        self._attr_native_min_value = -20
        self._attr_native_max_value = 20
        self._attr_native_step = 0.1

    @property
    def native_value(self):
        return float(self.controller.config.get('no_frost_temperature',0.0))

    async def async_set_native_value(self, value):
        self.controller.update_config('no_frost_temperature', float(value))