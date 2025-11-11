# Home Assistant Component for Climate Wire Pilot

Home Assistant Component for Climate Wire Pilot

## Introduction

Some ZHA thermostats (e.g. Legrand) are not recognized as a thermostat in Home Assistant but as a select entity.

This integration creates a `climate` entity using the `select` entity for easy control of your wire pilot heater.

## Installation

You can convert the `select` to a `climate` entity by searching "Climate Wire Pilot" in the integration page or helper page.

## YAML configuration

If you prefer to use `yaml`, you can, but it's not recommended as more and more integrations are moved to the UI. All the options are available in the UI.

| Key                | Type    | Required | Description                                                                                                               |
| :----------------- | :------ | :------- | :------------------------------------------------------------------------------------------------------------------------ |
| `platform`         | string  | yes      | Platform name                                                                                                             |
| `heater`           | string  | yes      | Light entity                                                                                                              |
| `sensor`           | string  | no       | Temperature sensor (for display)                                                                                          |
| `name`             | string  | no       | Name to use in the frontend.                                                                                              |
| `unique_id`        | string  | no       | An ID that uniquely identifies this climate. If two climates have the same unique ID, Home Assistant will raise an error. |

The unique id is recommended to allow icon, entity_id or name changes from the UI.

### Example

```yaml
climate:
  - platform: climate_wire_pilot
    heater: select.heater_living_room_modes
```

with optional sensor

```yaml
climate:
  - platform: climate_wire_pilot
    heater: select.heater_living_room_modes
    sensor: sensor.temperature_living_room
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

## Lovelace

You can use the [climate-mode-entity-row](https://github.com/piitaya/lovelace-climate-mode-entity-row) card in your lovelace dashboard to easily switch between modes.
