from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .controller import PoolController
from .select_mode import async_setup_select
from .sensor_runtime import async_setup_sensor

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    controller = PoolController(hass, entry.data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller

    await controller.initialize()
    await async_setup_select(hass, entry, controller)
    await async_setup_sensor(hass, entry, controller)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True