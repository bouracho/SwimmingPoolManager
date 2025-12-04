from datetime import datetime, timedelta, time
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change, async_call_later
from .const import MODES

def compute_filtration_duration(temp):
    return max(0, min(24, temp / 2))

class PoolController:
    def __init__(self, hass: HomeAssistant, cfg):
        self.hass = hass
        self.temp_entity = cfg.get('water_temperature_entity')
        self.pump_entity = cfg.get('pump_switch_entity')
        self.pivot_time = time.fromisoformat(cfg.get('pivot_time'))
        self.cut_duration = int(cfg.get('cut_duration'))
        self.break_duration = int(cfg.get('break_duration')) * 60
        self.anti_freeze_temp = float(cfg.get('anti_freeze_temperature'))
        self.mode = "ete"

    async def initialize(self):
        async_track_time_change(self.hass, self.handle_pivot,
                                hour=self.pivot_time.hour,
                                minute=self.pivot_time.minute,
                                second=0)

    async def handle_pivot(self, now):
        temp = self.get_temperature()
        if temp is None:
            return

        if self.mode == "off":
            await self.turn_off()
            return

        if self.mode == "continu":
            await self.turn_on()
            return

        if temp <= self.anti_freeze_temp:
            await self.turn_on()
            return

        if self.mode == "hiver":
            await self.turn_on()
            async_call_later(self.hass, self.cut_duration * 60, self.turn_off)
            return

        total_hours = compute_filtration_duration(temp)
        half = total_hours / 2

        # Convert hours to seconds
        half_sec = half * 3600

        pivot_dt = datetime.combine(datetime.now().date(), self.pivot_time)

        start_1 = pivot_dt - timedelta(seconds=half_sec)
        end_1 = pivot_dt

        start_2 = pivot_dt + timedelta(seconds=self.break_duration)
        end_2 = start_2 + timedelta(seconds=half_sec)

        await self.schedule_block(start_1, end_1)
        await self.schedule_block(start_2, end_2)

    async def schedule_block(self, start_dt, end_dt):
        now = datetime.now()

        if start_dt <= now <= end_dt:
            await self.turn_on()
            async_call_later(self.hass, (end_dt - now).total_seconds(), self.turn_off)
        elif now < start_dt:
            async_call_later(self.hass, (start_dt - now).total_seconds(), self.turn_on)
            async_call_later(self.hass, (end_dt - now).total_seconds(), self.turn_off)

    def get_temperature(self):
        state = self.hass.states.get(self.temp_entity)
        try:
            return float(state.state)
        except:
            return None

    async def turn_on(self, *_):
        await self.hass.services.async_call('switch', 'turn_on', {'entity_id': self.pump_entity})

    async def turn_off(self, *_):
        await self.hass.services.async_call('switch', 'turn_off', {'entity_id': self.pump_entity})
