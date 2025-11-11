# Home Assistant Component for Climate Wire Pilot

Home Assistant Component for Climate Wire Pilot

## Introduction

Some ZHA thermostats (e.g. Legrand) are not recognized as a thermostat in Home Assistant but as a select entity.

This integration creates a `climate` entity using the `select` entity for easy control of your wire pilot heater.

## Installation

You can convert the `select` to a `climate` entity by searching "Climate Wire Pilot" in the integration page or helper page.

## YAML configuration

If you prefer to use `yaml`, you can, but it's not recommended as more and more integrations are moved to the UI. All the options are available in the UI.

| Key                    | Type    | Required | Description                                                                                                               |
| :--------------------- | :------ | :------- | :------------------------------------------------------------------------------------------------------------------------ |
| `platform`             | string  | yes      | Platform name                                                                                                             |
| `heater`               | string  | yes      | Select entity for wire pilot control                                                                                      |
| `temperature_sensor`   | string  | no       | Temperature sensor (for display)                                                                                          |
| `power_sensor`         | string  | no       | Power sensor to monitor heater power consumption (for hvac_action)                                                        |
| `power_threshold`      | float   | no       | Power threshold in Watts above which the heater is considered to be heating (default: 0)                                  |
| `name`                 | string  | no       | Name to use in the frontend                                                                                               |
| `unique_id`            | string  | no       | An ID that uniquely identifies this climate. If two climates have the same unique ID, Home Assistant will raise an error. |

The unique id is recommended to allow icon, entity_id or name changes from the UI.

### Example

```yaml
climate:
  - platform: climate_wire_pilot
    heater: select.heater_living_room_modes
```

with optional temperature sensor

```yaml
climate:
  - platform: climate_wire_pilot
    heater: select.heater_living_room_modes
    temperature_sensor: sensor.temperature_living_room
```

with optional power sensor to monitor heating activity

```yaml
climate:
  - platform: climate_wire_pilot
    heater: select.heater_living_room_modes
    temperature_sensor: sensor.temperature_living_room
    power_sensor: sensor.heater_living_room_power
    power_threshold: 50  # Consider heating when power > 50W
```

### Unique ID

The `unique_id` is used to edit the entity from the GUI. It's automatically generated from heater entity_id. As the `unique_id` must be unique, you can not create 2 entities with the same heater.

If you want to have 2 climate with the same heater, you must specify the `unique_id` in the config.

```yaml
climate:
  - platform: climate_wire_pilot
    heater: select.heater_living_room_modes
    unique_id: climate_heater_living_room_1
  - platform: climate_wire_pilot
    heater: select.heater_living_room_modes
    unique_id: climate_heater_living_room_2
```

## Power Sensor & HVAC Action

You can optionally configure a power sensor to monitor the actual heating activity of your wire pilot heater. This feature allows the climate entity to display the real-time heating status (`hvac_action`):

- **HVAC Action: Heating** - When power consumption is above the configured threshold
- **HVAC Action: Idle** - When power consumption is below the threshold or the heater is off

### Configuration

1. Add a power sensor entity (e.g., from a smart plug or energy monitoring device)
2. Set a power threshold value in Watts (default: 0W)
   - The threshold determines when the heater is considered to be actively heating
   - Example: Set to 50W if your heater consumes more than 50W when heating

## Lovelace

You can use the [climate-mode-entity-row](https://github.com/piitaya/lovelace-climate-mode-entity-row) card in your lovelace dashboard to easily switch between modes.
