"""Piscine Manager integration - __init__.py"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .controller import PoolController
from .select_mode import async_setup_select
from .sensor_runtime import async_setup_sensor

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    LOGGER.info("Setting up Piscine Manager entry %s", entry.entry_id)

    controller = PoolController(hass, entry.data, entry.entry_id)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller

    await controller.initialize()

    # create UI entities
    await async_setup_select(hass, entry, controller)
    await async_setup_sensor(hass, entry, controller)

    # register service to set mode
    async def async_handle_set_mode(call):
        mode = call.data.get("mode")
        await controller.async_set_mode(mode)

    hass.services.async_register(DOMAIN, "set_mode", async_handle_set_mode)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    LOGGER.info("Unloading Piscine Manager entry %s", entry.entry_id)
    hass.services.async_remove(DOMAIN, "set_mode")
    controller = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if controller:
        await controller.shutdown()
    return True
