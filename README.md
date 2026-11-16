# Home Assistant Component for Climate Wire Pilot

![Climate Wire Pilot logo](custom_components/climate_wire_pilot/brand/icon.png)

[Version française](README.fr.md)

Home Assistant climate for wire pilot heaters: Qubino ZMNHJD1, Legrand and NodOn (ZHA, Zigbee2MQTT).

## Introduction

Some wire pilot modules are not recognized as a thermostat in Home Assistant:

- Zigbee modules (Legrand, NodOn, Adeo, VAV) are exposed as a `select` entity, by ZHA or Zigbee2MQTT.
- The Qubino ZMNHJD1 is exposed as a `light` entity, where the brightness selects the mode (see [Qubino and the light entity](#qubino-and-the-light-entity)).

This integration creates a `climate` entity from the `select` or `light` entity for easy control of your wire pilot heater.

The climate has 2 modes:

- `heat`, split into 5 presets:
  - `comfort`: "Comfort" mode
  - `comfort-1`: "Comfort -1" mode
  - `comfort-2`: "Comfort -2" mode
  - `eco`: "Eco" mode
  - `away`: "Frost protection" mode
- `off`: "Off" mode

## Compatible devices

| Device                                | Model             | ZHA | Zigbee2MQTT | Z-Wave JS |
| :------------------------------------ | :---------------- | :-- | :---------- | :-------- |
| Legrand cable outlet with pilot wire  | 064882            | ✅  | ✅          |           |
| NodOn pilot wire heating module       | SIN-4-FP-21       | ✅  | ✅          |           |
| NodOn pilot wire heating module       | SIN-4-FP-20       |     | ✅          |           |
| NodOn electrical heating actuator     | FPS-4-1-00        |     | ✅          |           |
| Adeo Equation pilot wire module       | SIN-4-FP-21_EQU   | ✅  | ✅          |           |
| VAV pilot wire heating module         | VAV-256215-MOD1   |     | ✅          |           |
| Qubino Flush Pilot Wire               | ZMNHJD1           |     |             | ✅        |

The Legrand cable outlet must be switched to pilot wire mode first: set its "Device mode" to pilot wire in ZHA, or `device_mode` to `pilot_on` in Zigbee2MQTT.

If your module can't be picked when adding a thermostat, open an issue with the options of its `select` entity.

## Installation

### HACS

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=piitaya&repository=ha-climate-wire-pilot&category=integration)

Or in HACS, add `https://github.com/piitaya/ha-climate-wire-pilot` as a custom repository with the "Integration" type. Then download Climate Wire Pilot and restart Home Assistant.

### Manual

Copy the `custom_components/climate_wire_pilot` folder into the `custom_components` folder of your Home Assistant configuration, then restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up Climate Wire Pilot.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=climate_wire_pilot)

Or search "Climate Wire Pilot" in the integration page or helper page, then pick the `select` or `light` entity of your heater.

## Power Sensor & HVAC Action

You can optionally configure a power sensor to monitor the actual heating activity of your wire pilot heater. This feature allows the climate entity to display the real-time heating status (`hvac_action`):

- **HVAC Action: Heating** - When power consumption is above the configured threshold
- **HVAC Action: Idle** - When power consumption is below the threshold

When the heater is off, the action is always "Off", with or without a power sensor.

### Setup

1. Add a power sensor entity (e.g., from a smart plug or energy monitoring device)
2. Set a power threshold value in Watts (default: 0W)
   - The threshold determines when the heater is considered to be actively heating
   - Example: Set to 50W if your heater consumes more than 50W when heating

## Qubino and the light entity

The Qubino ZMNHJD1 doesn't use a dedicated Z-Wave command for the pilot wire. It reuses the command meant for dimmers, and each 10% range of the dimmer level selects a mode. Z-Wave JS can't tell the difference, so Home Assistant shows the module as a dimmable light. Turning it "off" or setting its brightness from a light card actually changes the heater mode.

This integration hides that light and translates the brightness for you:

| Mode             | Brightness |
| :--------------- | :--------- |
| Off              | 0 to 10%   |
| Frost protection | 11 to 20%  |
| Eco              | 21 to 30%  |
| Comfort -2       | 31 to 40%  |
| Comfort -1       | 41 to 50%  |
| Comfort          | 51 to 100% |

When adding a thermostat, only lights from a Qubino device are listed.

## YAML configuration

YAML configuration is deprecated. Existing `climate_wire_pilot` platforms in `configuration.yaml` are imported into the UI on startup, keeping their entity ID and name. A repair issue then asks you to remove them from `configuration.yaml`.
