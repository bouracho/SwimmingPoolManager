"""Binary sensors: filtration_active and frost_protection_active"""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    entities = [FiltrationActiveBinarySensor(controller, entry.entry_id), FrostProtectionBinarySensor(controller, entry.entry_id)]
    async_add_entities(entities)

class FiltrationActiveBinarySensor(BinarySensorEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Pool Filtration Active {entry_id}"
        self._attr_unique_id = f"{entry_id}_filtration_active_bs"

    @property
    def is_on(self):
        return bool(self.controller.data.get('filtration_active'))

class FrostProtectionBinarySensor(BinarySensorEntity):
    def __init__(self, controller, entry_id):
        self.controller = controller
        self._attr_name = f"Pool Frost Protection {entry_id}"
        self._attr_unique_id = f"{entry_id}_frost_bs"

    @property
    def is_on(self):
        return self.controller.data.get('mode') == 'frost'
