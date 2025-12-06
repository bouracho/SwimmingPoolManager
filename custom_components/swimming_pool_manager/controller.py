"""Controller that coordinates schedule, frost protection and updates."""
import logging
from datetime import datetime
from homeassistant.helpers.event import async_track_time_change, async_call_later
from .calculation import compute_filtration_duration_cubic, compute_schedule_windows, check_frost_protection
from .const import DOMAIN

LOGGER = logging.getLogger(__name__)

class PoolController:
    def __init__(self, hass, config: dict, entry_id: str):
        self.hass = hass
        self.entry_id = entry_id
        self.config = config
        self.mode = 'ete'
        self._scheduled = []
        self.data = { 'filtration_active': False, 'mode': None }

    async def initialize(self):
        pivot = self.config.get('pivot_hour')
        if pivot:
            h, m = pivot.split(':') if ':' in pivot else (pivot, '00')
            async_track_time_change(self.hass, self._handle_pivot, hour=int(h), minute=int(m), second=0)
        LOGGER.info("PoolController(%s) initialized", self.entry_id)
        await self._handle_pivot(datetime.now())

    async def shutdown(self):
        for cancel in self._scheduled:
            try:
                cancel()
            except Exception:
                pass
        self._scheduled.clear()

    async def async_set_mode(self, mode: str):
        LOGGER.info("Set mode %s", mode)
        self.mode = mode
        await self._handle_pivot(datetime.now())

    def update_config(self, key, value):
        LOGGER.info("Update config %s=%s", key, value)
        self.config[key] = value

    async def _handle_pivot(self, now):
        LOGGER.debug("Handle pivot at %s", now)
        # clear previous schedules
        for c in self._scheduled:
            try:
                c()
            except Exception:
                pass
        self._scheduled.clear()

        # read temps
        temp_state = self.hass.states.get(self.config.get('water_temp_sensor'))
        outdoor_state = self.hass.states.get(self.config.get('outdoor_temp_entity'))
        try:
            temp = float(temp_state.state) if temp_state else None
        except Exception:
            temp = None
        try:
            outdoor = float(outdoor_state.state) if outdoor_state else None
        except Exception:
            outdoor = None

        # Frost protection
        if check_frost_protection(outdoor, self.config.get('no_frost_temperature', 0.0)):
            LOGGER.warning("Frost protection active - forcing pump ON")
            self.data['filtration_active'] = True
            self.data['mode'] = 'frost'
            # schedule remains until temp above threshold — implement periodic re-check
            return

        # respect modes
        if self.mode == 'off':
            self.data['filtration_active'] = False
            self.data['mode'] = 'off'
            return
        if self.mode == 'continu':
            self.data['filtration_active'] = True
            self.data['mode'] = 'continu'
            return
        if self.mode == 'hiver':
            # run short cycle
            self.data['filtration_active'] = True
            self.data['mode'] = 'hiver'
            # schedule off after cut_duration
            handle = async_call_later(self.hass, int(self.config.get('cut_duration_minutes',60))*60, self._end_hiver)
            self._scheduled.append(handle)
            return

        # ete: compute duration and schedule two windows
        if temp is None:
            LOGGER.warning("No water temperature available")
            return
        coef = int(self.config.get('adjust_coeff_pct',100))
        total_hours = compute_filtration_duration_cubic(temp, coef)
        windows = compute_schedule_windows(self.config.get('pivot_hour'), int(self.config.get('pause_minutes',0)), total_hours)

        self.data['filtration_active'] = False
        self.data['mode'] = 'ete'
        self.data['schedule_windows'] = windows

        # schedule actions
        now_dt = datetime.now()
        for start, end in windows:
            if start <= now_dt <= end:
                # turn on until end
                await self.hass.services.async_call('switch','turn_on',{'entity_id': self.config.get('pump_switch')})
                handle = async_call_later(self.hass, (end - now_dt).total_seconds(), self._turn_off_pump)
                self._scheduled.append(handle)
                self.data['filtration_active'] = True
            elif now_dt < start:
                # schedule on/off
                handle_on = async_call_later(self.hass, (start - now_dt).total_seconds(), self._turn_on_pump)
                handle_off = async_call_later(self.hass, (end - now_dt).total_seconds(), self._turn_off_pump)
                self._scheduled.extend([handle_on, handle_off])

    async def _turn_on_pump(self, *_):
        await self.hass.services.async_call('switch','turn_on',{'entity_id': self.config.get('pump_switch')})
        self.data['filtration_active'] = True

    async def _turn_off_pump(self, *_):
        await self.hass.services.async_call('switch','turn_off',{'entity_id': self.config.get('pump_switch')})
        self.data['filtration_active'] = False

    async def _end_hiver(self, *_):
        await self._turn_off_pump()
        self.data['mode'] = 'ete'