"""Pump and robot switch entities — rely on controller scheduling."""
import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    conf = entry.data
    entities = [PoolPumpSwitch(hass, conf, entry.entry_id)]
    if conf.get('robot_enabled') and conf.get('robot_switch'):
        entities.append(PoolRobotSwitch(hass, conf, entry.entry_id))
    async_add_entities(entities)

class PoolPumpSwitch(SwitchEntity):
    def __init__(self, hass, conf, entry_id):
        self.hass = hass
        self.conf = conf
        self.entry_id = entry_id
        self._attr_name = "Pool Pump"
        self._attr_unique_id = f"{entry_id}_pump"
        self._is_on = False

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        pump = self.conf.get('pump_switch')
        LOGGER.info("Turning pump ON (%s)", pump)
        await self.hass.services.async_call('switch','turn_on',{'entity_id': pump})
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        pump = self.conf.get('pump_switch')
        LOGGER.info("Turning pump OFF (%s)", pump)
        await self.hass.services.async_call('switch','turn_off',{'entity_id': pump})
        self._is_on = False

    async def async_update(self):
        # reflect controller recommended state
        controller = self.hass.data.get(DOMAIN, {}).get(self.entry_id)
        if controller and controller.data.get('mode') == 'frost':
            # frost mode forces pump on
            if not self._is_on:
                await self.async_turn_on()
            return
        # otherwise do nothing; controller schedules via service calls

class PoolRobotSwitch(SwitchEntity):
    def __init__(self, hass, conf, entry_id):
        self.hass = hass
        self.conf = conf
        self.entry_id = entry_id
        self._attr_name = "Pool Robot"
        self._attr_unique_id = f"{entry_id}_robot"

    @property
    def is_on(self):
        robot = self.conf.get('robot_switch')
        if not robot:
            return False
        state = self.hass.states.get(robot)
        return state and state.state == 'on'

    async def async_turn_on(self, **kwargs):
        robot = self.conf.get('robot_switch')
        if robot:
            await self.hass.services.async_call('switch','turn_on',{'entity_id': robot})

    async def async_turn_off(self, **kwargs):
        robot = self.conf.get('robot_switch')
        if robot:
            await self.hass.services.async_call('switch','turn_off',{'entity_id': robot})
