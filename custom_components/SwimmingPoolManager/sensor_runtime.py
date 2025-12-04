"""Sensor exposing computed filtration duration (hours) and next cycle times."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import async_get_current_platform
from .controller import compute_filtration_curve

LOGGER = logging.getLogger(__name__)

async def async_setup_sensor(hass, entry, controller):
    platform = async_get_current_platform()
    entity = RuntimeSensor(controller, entry.entry_id)
    platform.add_entities([entity])
    LOGGER.debug("Runtime sensor created for entry %s", entry.entry_id)

class RuntimeSensor(SensorEntity):
    def __init__(self, controller, entry_id):
        self._controller = controller
        self._entry_id = entry_id
        self._attr_name = f"Piscine Runtime {entry_id}"
        self._attr_unit_of_measurement = "h"

    @property
    def unique_id(self):
        return f"piscine_runtime_{self._entry_id}"

    @property
    def state(self):
        temp = self._controller._get_temp()
        if temp is None:
            return 0
        try:
            return compute_filtration_curve(temp)
        except Exception:
            LOGGER.exception("Failed computing runtime")
            return 0