"""Climate Scheduler - Smart temperature scheduling for Home Assistant."""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_SCHEDULES,
    CONF_PRESETS,
    DEFAULT_NAME,
    DOMAIN,
    SCHEDULE_WEEKDAY,
    SCHEDULE_WEEKEND,
    PRESET_HOME,
    PRESET_AWAY,
    PRESET_SLEEP,
    PRESET_VACATION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Climate Scheduler from a config entry."""
    async_add_entities([ClimateSchedulerEntity(hass, entry)])


class ClimateSchedulerEntity(ClimateEntity, RestoreEntity):
    """Representation of a Climate Scheduler."""

    _attr_has_entity_name = True
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL, HVACMode.OFF]
    _attr_preset_modes = [PRESET_HOME, PRESET_AWAY, PRESET_SLEEP, PRESET_VACATION]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the climate scheduler."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.data.get(CONF_NAME, DEFAULT_NAME)
        
        # Configuration
        self._climate_entity = entry.data.get(CONF_CLIMATE_ENTITY)
        self._schedules = entry.options.get(CONF_SCHEDULES, entry.data.get(CONF_SCHEDULES, {}))
        self._presets = entry.options.get(CONF_PRESETS, entry.data.get(CONF_PRESETS, {}))
        
        # State
        self._attr_current_temperature: float | None = None
        self._attr_target_temperature: float | None = None
        self._attr_hvac_mode = HVACMode.HEAT_COOL
        self._attr_preset_mode = PRESET_HOME
        self._attr_hvac_action = HVACAction.IDLE
        
        # Schedule tracking
        self._unsubscribe_time_listener = None
        self._last_preset_change: datetime | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="Shadow",
            model="Climate Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "scheduled_entity": self._climate_entity,
            "active_preset": self._attr_preset_mode,
            "next_schedule": self._get_next_schedule(),
            "next_temperature": self._get_next_temperature(),
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                try:
                    self._attr_target_temperature = float(last_state.attributes.get("temperature", 21))
                    self._attr_preset_mode = last_state.attributes.get("preset_mode", PRESET_HOME)
                except (ValueError, TypeError):
                    pass

        # Set up schedule checker
        self._unsubscribe_time_listener = async_track_time_change(
            self.hass,
            self._async_check_schedule,
            minute=range(0, 60, 5),  # Check every 5 minutes
            second=0,
        )
        
        # Initial schedule check
        await self._async_check_schedule(None)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity is removed from hass."""
        if self._unsubscribe_time_listener:
            self._unsubscribe_time_listener()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if temperature := kwargs.get(ATTR_TEMPERATURE):
            self._attr_target_temperature = temperature
            await self._async_apply_to_climate_entity()
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        self._attr_hvac_mode = hvac_mode
        await self._async_apply_to_climate_entity()
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self._attr_preset_modes:
            _LOGGER.warning("Invalid preset mode: %s", preset_mode)
            return
            
        self._attr_preset_mode = preset_mode
        self._last_preset_change = datetime.now()
        
        # Apply preset temperature immediately
        preset_temp = self._presets.get(preset_mode, {}).get("temperature", 21)
        self._attr_target_temperature = preset_temp
        
        await self._async_apply_to_climate_entity()
        self.async_write_ha_state()

    @callback
    async def _async_check_schedule(self, now: datetime | None) -> None:
        """Check if schedule needs to change preset."""
        if not self._schedules:
            return

        current_time = datetime.now().time()
        current_day = datetime.now().weekday()
        
        # Determine if weekday or weekend
        schedule_type = SCHEDULE_WEEKDAY if current_day < 5 else SCHEDULE_WEEKEND
        day_schedule = self._schedules.get(schedule_type, [])
        
        if not day_schedule:
            return

        # Find current time slot
        active_preset = None
        for slot in sorted(day_schedule, key=lambda x: x.get("time", "00:00")):
            slot_time = datetime.strptime(slot.get("time", "00:00"), "%H:%M").time()
            if current_time >= slot_time:
                active_preset = slot.get("preset")
            else:
                break

        if active_preset and active_preset != self._attr_preset_mode:
            # Check for manual override (don't change if user manually set in last 30 min)
            if self._last_preset_change:
                minutes_since_manual = (datetime.now() - self._last_preset_change).total_seconds() / 60
                if minutes_since_manual < 30:
                    _LOGGER.debug("Manual override active, skipping schedule change")
                    return
            
            _LOGGER.info(
                "Schedule changing preset from %s to %s",
                self._attr_preset_mode,
                active_preset,
            )
            await self.async_set_preset_mode(active_preset)

    async def _async_apply_to_climate_entity(self) -> None:
        """Apply current settings to the underlying climate entity."""
        if not self._climate_entity:
            return

        try:
            if self._attr_target_temperature is not None:
                await self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {
                        "entity_id": self._climate_entity,
                        "temperature": self._attr_target_temperature,
                    },
                    blocking=False,
                )
            
            if self._attr_hvac_mode is not None:
                await self.hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {
                        "entity_id": self._climate_entity,
                        "hvac_mode": self._attr_hvac_mode,
                    },
                    blocking=False,
                )
        except Exception as err:
            _LOGGER.error("Failed to apply settings to %s: %s", self._climate_entity, err)

    def _get_next_schedule(self) -> str | None:
        """Get the next scheduled change time."""
        current_time = datetime.now().time()
        current_day = datetime.now().weekday()
        schedule_type = SCHEDULE_WEEKDAY if current_day < 5 else SCHEDULE_WEEKEND
        day_schedule = self._schedules.get(schedule_type, [])
        
        for slot in sorted(day_schedule, key=lambda x: x.get("time", "00:00")):
            slot_time = datetime.strptime(slot.get("time", "00:00"), "%H:%M").time()
            if current_time < slot_time:
                return slot.get("time")
        return None

    def _get_next_temperature(self) -> float | None:
        """Get the temperature for the next schedule."""
        current_time = datetime.now().time()
        current_day = datetime.now().weekday()
        schedule_type = SCHEDULE_WEEKDAY if current_day < 5 else SCHEDULE_WEEKEND
        day_schedule = self._schedules.get(schedule_type, [])
        
        for slot in sorted(day_schedule, key=lambda x: x.get("time", "00:00")):
            slot_time = datetime.strptime(slot.get("time", "00:00"), "%H:%M").time()
            if current_time < slot_time:
                preset = slot.get("preset")
                return self._presets.get(preset, {}).get("temperature")
        return None
