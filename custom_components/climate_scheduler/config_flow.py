"""Config flow for Climate Scheduler integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_SCHEDULES,
    CONF_PRESETS,
    DEFAULT_NAME,
    DOMAIN,
    PRESET_HOME,
    PRESET_AWAY,
    PRESET_SLEEP,
    PRESET_VACATION,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCHEDULES = {
    "weekday": [
        {"time": "06:00", "preset": PRESET_HOME},
        {"time": "08:00", "preset": PRESET_AWAY},
        {"time": "17:00", "preset": PRESET_HOME},
        {"time": "22:00", "preset": PRESET_SLEEP},
    ],
    "weekend": [
        {"time": "08:00", "preset": PRESET_HOME},
        {"time": "23:00", "preset": PRESET_SLEEP},
    ],
}

DEFAULT_PRESETS = {
    PRESET_HOME: {"temperature": 21},
    PRESET_AWAY: {"temperature": 18},
    PRESET_SLEEP: {"temperature": 19},
    PRESET_VACATION: {"temperature": 16},
}


class ClimateSchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Climate Scheduler."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CLIMATE_ENTITY])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
                options={
                    CONF_SCHEDULES: DEFAULT_SCHEDULES,
                    CONF_PRESETS: DEFAULT_PRESETS,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_CLIMATE_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=CLIMATE_DOMAIN)
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ClimateSchedulerOptionsFlow:
        """Create the options flow."""
        return ClimateSchedulerOptionsFlow(config_entry)


class ClimateSchedulerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Climate Scheduler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        presets = self.config_entry.options.get(CONF_PRESETS, DEFAULT_PRESETS)
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        f"temp_{PRESET_HOME}",
                        default=presets.get(PRESET_HOME, {}).get("temperature", 21),
                    ): vol.All(vol.Coerce(float), vol.Range(min=5, max=35)),
                    vol.Required(
                        f"temp_{PRESET_AWAY}",
                        default=presets.get(PRESET_AWAY, {}).get("temperature", 18),
                    ): vol.All(vol.Coerce(float), vol.Range(min=5, max=35)),
                    vol.Required(
                        f"temp_{PRESET_SLEEP}",
                        default=presets.get(PRESET_SLEEP, {}).get("temperature", 19),
                    ): vol.All(vol.Coerce(float), vol.Range(min=5, max=35)),
                    vol.Required(
                        f"temp_{PRESET_VACATION}",
                        default=presets.get(PRESET_VACATION, {}).get("temperature", 16),
                    ): vol.All(vol.Coerce(float), vol.Range(min=5, max=35)),
                }
            ),
        )
