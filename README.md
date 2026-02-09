# Climate Scheduler

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/iret33/ha-climate-scheduler.svg)](https://github.com/iret33/ha-climate-scheduler/releases)
[![License](https://img.shields.io/github/license/iret33/ha-climate-scheduler.svg)](LICENSE)

Smart climate scheduler with time-based temperature profiles for Home Assistant. Automatically control your thermostat based on schedules and presets.

## Features

- **4 Built-in Presets**: Home, Away, Sleep, Vacation with configurable temperatures
- **Weekday/Weekend Schedules**: Different schedules for work days vs weekends
- **Manual Override Protection**: Manual changes are respected for 30 minutes
- **Config Flow Setup**: Easy UI-based configuration
- **Service Calls**: Programmatically control presets and schedules
- **Next Schedule Display**: See upcoming temperature changes in attributes

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click "Custom Repositories"
3. Add `https://github.com/iret33/ha-climate-scheduler`
4. Category: Integration
5. Install and restart Home Assistant

### Manual

1. Copy `custom_components/climate_scheduler/` to your Home Assistant `custom_components/` folder
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Climate Scheduler"
3. Select your climate entity to control
4. Configure preset temperatures via **Configure**

### Default Schedule

| Time | Weekday Preset | Weekend Preset |
|------|----------------|----------------|
| 06:00 | Home | - |
| 08:00 | Away | Home |
| 17:00 | Home | - |
| 22:00 | Sleep | - |
| 23:00 | - | Sleep |

## Services

### `climate_scheduler.apply_preset`

Apply a preset mode manually (bypasses schedule for 30 minutes).

```yaml
service: climate_scheduler.apply_preset
target:
  entity_id: climate.living_room_scheduler
data:
  preset: away
```

### `climate_scheduler.enable_schedule`

Re-enable automatic schedule control.

### `climate_scheduler.disable_schedule`

Disable automatic schedule control.

### `climate_scheduler.set_schedule`

Update the schedule programmatically.

```yaml
service: climate_scheduler.set_schedule
target:
  entity_id: climate.living_room_scheduler
data:
  schedule_type: weekday
  schedule:
    - time: "07:00"
      preset: home
    - time: "09:00"
      preset: away
```

## State Attributes

| Attribute | Description |
|-----------|-------------|
| `scheduled_entity` | The underlying climate entity being controlled |
| `active_preset` | Currently active preset mode |
| `next_schedule` | Time of next scheduled change |
| `next_temperature` | Temperature of next scheduled change |

## Support

- [Issue Tracker](https://github.com/iret33/ha-climate-scheduler/issues)
- [Documentation](https://github.com/iret33/ha-climate-scheduler)

## License

MIT License - See [LICENSE](LICENSE) for details.
