"""Constants for the Climate Scheduler integration."""

from typing import Final

DOMAIN: Final = "climate_scheduler"
DEFAULT_NAME: Final = "Climate Scheduler"

# Configuration keys
CONF_CLIMATE_ENTITY: Final = "climate_entity"
CONF_SCHEDULES: Final = "schedules"
CONF_PRESETS: Final = "presets"

# Schedule types
SCHEDULE_WEEKDAY: Final = "weekday"
SCHEDULE_WEEKEND: Final = "weekend"

# Preset modes
PRESET_HOME: Final = "home"
PRESET_AWAY: Final = "away"
PRESET_SLEEP: Final = "sleep"
PRESET_VACATION: Final = "vacation"

# Services
SERVICE_SET_SCHEDULE: Final = "set_schedule"
SERVICE_APPLY_PRESET: Final = "apply_preset"
SERVICE_ENABLE_SCHEDULE: Final = "enable_schedule"
SERVICE_DISABLE_SCHEDULE: Final = "disable_schedule"

# Attributes
ATTR_SCHEDULE_ENABLED: Final = "schedule_enabled"
ATTR_SCHEDULE_TYPE: Final = "schedule_type"
ATTR_PRESET: Final = "preset"
