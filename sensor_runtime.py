from homeassistant.components.sensor import SensorEntity
from .controller import compute_filtration_duration

async def async_setup_sensor(hass, entry, controller):
    entity = RuntimeSensor(controller, entry.entry_id)
    hass.helpers.entity_platform.async_get_current_platform().add_entities([entity])

class RuntimeSensor(SensorEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Piscine Runtime {entry_id}"
        self._attr_unit_of_measurement = "h"

    @property
    def state(self):
        temp = self.controller.get_temperature()
        if temp is None:
            return 0
        return compute_filtration_duration(temp)