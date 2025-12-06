"""Sensor exposing filtration hours and windows."""
import logging
from homeassistant.components.sensor import SensorEntity
from .calculation import compute_filtration_duration_cubic, compute_schedule_windows

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([PoolFiltrationSensor(hass, entry.data, entry.entry_id)])

class PoolFiltrationSensor(SensorEntity):
    def __init__(self, hass, conf, entry_id):
        self.hass = hass
        self.conf = conf
        self.entry_id = entry_id
        self._attr_name = "Pool Filtration Hours"
        self._attr_unique_id = f"{entry_id}_filtration_hours"
        self._state = None
        self._attrs = {}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    async def async_update(self):
        temp_entity = self.conf.get('water_temp_sensor')
        temp_state = self.hass.states.get(temp_entity)
        if not temp_state:
            self._state = None
            self._attrs = {}
            return
        try:
            t = float(temp_state.state)
        except Exception:
            self._state = None
            self._attrs = {}
            return

        coef = int(self.conf.get('adjust_coeff_pct',100))
        pause = int(self.conf.get('pause_minutes',0))
        pivot = self.conf.get('pivot_hour')

        hours = compute_filtration_duration_cubic(t, coef)
        windows = compute_schedule_windows(pivot, pause, hours)

        self._state = round(hours,2)
        self._attrs = {
            'pivot': pivot,
            'pause_minutes': pause,
            'coef_pct': coef,
            'windows': [{ 'start': w[0].isoformat(), 'end': w[1].isoformat() } for w in windows]
        }
