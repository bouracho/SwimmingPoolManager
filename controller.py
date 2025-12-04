"""Main controller logic for Pool management."""
import logging
from datetime import datetime, timedelta, time
from typing import Optional
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change, async_call_later
from homeassistant.const import STATE_ON, STATE_OFF
from .const import MODES, CONF_ROBOT_ENABLED, CONF_ROBOT_SWITCH

LOGGER = logging.getLogger(__name__)

# Curve-based model (example): mapping temperature ranges to hours
def compute_filtration_curve(temp: float) -> float:
    """Return filtration duration in hours according to a curve model."""
    try:
        if temp is None:
            return 0.0
        t = float(temp)
        if t <= 10:
            return 2.0
        if t <= 15:
            return 4.0
        if t <= 20:
            return 6.0
        if t <= 25:
            return 8.0
        if t <= 30:
            return 10.0
        return 12.0
    except Exception:  # defensive
        LOGGER.exception("Error computing filtration curve")
        return 0.0

class PoolController:
    def __init__(self, hass: HomeAssistant, cfg: dict, entry_id: str):
        self.hass = hass
        self.entry_id = entry_id
        self.temp_entity = cfg.get('water_temperature_entity')
        self.pump_entity = cfg.get('pump_switch_entity')
        self.pivot_time = time.fromisoformat(cfg.get('pivot_time'))
        self.cut_duration = int(cfg.get('cut_duration'))
        self.break_duration_minutes = int(cfg.get('break_duration', 0))
        self.anti_freeze_temp = float(cfg.get('anti_freeze_temperature'))
        self.robot_enabled = cfg.get(CONF_ROBOT_ENABLED, False)
        self.robot_switch = cfg.get(CONF_ROBOT_SWITCH)
        self.mode = 'ete'
        self._scheduled_handles = []

        LOGGER.debug("PoolController(%s) init: temp=%s pump=%s pivot=%s", entry_id, self.temp_entity, self.pump_entity, self.pivot_time)

    async def initialize(self):
        # Register daily pivot trigger
        async_track_time_change(self.hass, self.handle_pivot, hour=self.pivot_time.hour, minute=self.pivot_time.minute, second=0)
        LOGGER.info("PoolController(%s) initialized: pivot %s", self.entry_id, self.pivot_time)
        # Evaluate immediately once at startup
        await self.handle_pivot(datetime.now())

    async def shutdown(self):
        # cancel scheduled handles
        for h in self._scheduled_handles:
            try:
                h()
            except Exception:
                pass
        self._scheduled_handles.clear()
        LOGGER.info("PoolController(%s) shutdown", self.entry_id)

    async def async_set_mode(self, mode: str):
        LOGGER.info("PoolController(%s) set_mode %s", self.entry_id, mode)
        if mode in MODES:
            self.mode = mode
        else:
            LOGGER.warning("Unknown mode requested: %s", mode)

    def _get_temp(self) -> Optional[float]:
        state = self.hass.states.get(self.temp_entity)
        try:
            return float(state.state) if state else None
        except Exception:
            LOGGER.exception("Failed to read temperature from %s", self.temp_entity)
            return None

    async def handle_pivot(self, now):
        LOGGER.debug("handle_pivot called at %s", now)
        temp = self._get_temp()
        if temp is None:
            LOGGER.warning("No temperature available, aborting pivot handling")
            return

        # Cancel previous scheduled actions
        for cancel in self._scheduled_handles:
            try:
                cancel()
            except Exception:
                pass
        self._scheduled_handles = []

        # Mode handling
        if self.mode == 'off':
            LOGGER.info("Mode off — ensuring pump off")
            await self._turn_off()
            return

        if self.mode == 'continu':
            LOGGER.info("Mode continu — ensuring pump on")
            await self._turn_on()
            return

        # Anti-freeze has the highest priority
        if temp <= self.anti_freeze_temp:
            LOGGER.info("Anti-freeze triggered (temp=%s <= %s) — turning pump on", temp, self.anti_freeze_temp)
            await self._turn_on()
            return

        if self.mode == 'hiver':
            LOGGER.info("Mode hiver — running a short cycle of %s minutes", self.cut_duration)
            await self._turn_on()
            # schedule off after cut_duration minutes
            handle = async_call_later(self.hass, self.cut_duration * 60, self._turn_off)
            self._scheduled_handles.append(handle)
            return

        # ete: compute curve-based duration and split symmetrically around pivot with a break
        total_hours = compute_filtration_curve(temp)
        LOGGER.debug("Temp=%s => total_hours=%s", temp, total_hours)
        half_hours = total_hours / 2.0

        # compute datetimes
        pivot_dt = datetime.combine(datetime.now().date(), self.pivot_time)
        half_td = timedelta(hours=half_hours)
        break_td = timedelta(minutes=self.break_duration_minutes)

        start1 = pivot_dt - half_td - timedelta(seconds=0)
        end1 = pivot_dt - break_td/2 if self.break_duration_minutes else pivot_dt

        # per user request: pivot is not a start point; we center around pivot and insert a break
        # start1 .. end1  then start2 = end1 + break_duration then end2 = start2 + half_hours
        end1 = pivot_dt - timedelta(minutes=self.break_duration_minutes/2) if self.break_duration_minutes else pivot_dt
        start2 = pivot_dt + timedelta(minutes=self.break_duration_minutes/2) if self.break_duration_minutes else pivot_dt
        end2 = start2 + half_td

        LOGGER.debug("Scheduling blocks: %s->%s and %s->%s", start1, end1, start2, end2)

        # Schedule block 1
        await self._schedule_block(start1, end1)
        # Schedule block 2
        await self._schedule_block(start2, end2)

        # Optionally schedule robot after filtration if enabled
        if self.robot_enabled and self.robot_switch:
            # schedule robot run after end2
            async def start_robot(_):
                LOGGER.info("Starting robot %s", self.robot_switch)
                await self.hass.services.async_call('switch', 'turn_on', {'entity_id': self.robot_switch})
            handle = async_call_later(self.hass, (end2 - datetime.now()).total_seconds(), start_robot)
            self._scheduled_handles.append(handle)

    async def _schedule_block(self, start_dt: datetime, end_dt: datetime):
        now = datetime.now()
        # if already in the block, start now and stop at end
        if start_dt <= now <= end_dt:
            LOGGER.info("We are inside block [%s - %s], turning pump on until %s", start_dt, end_dt)
            await self._turn_on()
            handle = async_call_later(self.hass, (end_dt - now).total_seconds(), self._turn_off)
            self._scheduled_handles.append(handle)
        elif now < start_dt:
            # schedule turn_on at start_dt
            LOGGER.info("Scheduling pump on at %s and off at %s", start_dt, end_dt)
            handle_on = async_call_later(self.hass, (start_dt - now).total_seconds(), self._turn_on)
            handle_off = async_call_later(self.hass, (end_dt - now).total_seconds(), self._turn_off)
            self._scheduled_handles.extend([handle_on, handle_off])
        else:
            LOGGER.debug("Block %s-%s is in the past", start_dt, end_dt)

    async def _turn_on(self, *_):
        LOGGER.info("Turning pump on: %s", self.pump_entity)
        await self.hass.services.async_call('switch', 'turn_on', {'entity_id': self.pump_entity})

    async def _turn_off(self, *_):
        LOGGER.info("Turning pump off: %s", self.pump_entity)
        await self.hass.services.async_call('switch', 'turn_off', {'entity_id': self.pump_entity})
