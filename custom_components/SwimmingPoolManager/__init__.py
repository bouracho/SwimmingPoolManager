"""Pool Manager integration init."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .controller import PoolController

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    LOGGER.info("Setting up Pool Manager entry %s", entry.entry_id)

    hass.data.setdefault(DOMAIN, {})
    controller = PoolController(hass, entry.data, entry.entry_id)
    hass.data[DOMAIN][entry.entry_id] = controller

    await controller.initialize()

    # forward platforms
    for platform in ["sensor","switch","binary_sensor","number","select"]:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, platform))

    async def handle_set_mode(call):
        mode = call.data.get("mode")
        await controller.async_set_mode(mode)

    hass.services.async_register(DOMAIN, "set_mode", handle_set_mode)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    LOGGER.info("Unloading Pool Manager entry %s", entry.entry_id)
    for platform in ["sensor","switch","binary_sensor","number","select"]:
        await hass.config_entries.async_forward_entry_unload(entry, platform)

    hass.services.async_remove(DOMAIN, "set_mode")
    controller = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if controller:
        await controller.shutdown()
    return True