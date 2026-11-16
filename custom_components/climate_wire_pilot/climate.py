"""Platform for Climate Wire Pilot."""

import logging
import math

import voluptuous as vol

from homeassistant.components.climate import (
    PLATFORM_SCHEMA as CLIMATE_PLATFORM_SCHEMA,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    DOMAIN as LIGHT_DOMAIN,
    SERVICE_TURN_ON as LIGHT_SERVICE_TURN_ON,
)
from homeassistant.components.select import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    CONF_UNIQUE_ID,
    EVENT_HOMEASSISTANT_START,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import (
    CoreState,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
    split_entity_id,
)
from homeassistant.helpers import entity_registry as er, issue_registry as ir
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import CONF_HEATER, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_POWER_SENSOR = "power_sensor"
CONF_POWER_THRESHOLD = "power_threshold"

HEATER_DOMAINS = [LIGHT_DOMAIN, SELECT_DOMAIN]

PRESET_COMFORT_1 = "comfort-1"
PRESET_COMFORT_2 = "comfort-2"

# Select options of each preset, as named by ZHA and Zigbee2MQTT
PRESET_SELECT_OPTIONS = {
    PRESET_NONE: ("Off", "off"),
    PRESET_AWAY: ("FrostProtection", "frost_protection"),
    PRESET_ECO: ("Eco", "eco"),
    PRESET_COMFORT_2: ("ComfortMinus2", "comfort_-2"),
    PRESET_COMFORT_1: ("ComfortMinus1", "comfort_-1"),
    PRESET_COMFORT: ("Comfort", "comfort"),
}

SELECT_OPTION_TO_PRESET = {
    option: preset
    for preset, options in PRESET_SELECT_OPTIONS.items()
    for option in options
}

# Light brightness (0-99) upper bound of each preset
LIGHT_VALUE_TO_PRESET = [
    (10, PRESET_NONE),
    (20, PRESET_AWAY),
    (30, PRESET_ECO),
    (40, PRESET_COMFORT_2),
    (50, PRESET_COMFORT_1),
    (99, PRESET_COMFORT),
]

PRESET_TO_LIGHT_VALUE = {preset: value for value, preset in LIGHT_VALUE_TO_PRESET}

PLATFORM_SCHEMA_COMMON = vol.Schema(
    {
        vol.Required(CONF_HEATER): cv.entity_domain(HEATER_DOMAINS),
        vol.Optional(CONF_TEMPERATURE_SENSOR): cv.entity_id,
        vol.Optional(CONF_POWER_SENSOR): cv.entity_id,
        vol.Optional(CONF_POWER_THRESHOLD): vol.Coerce(float),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = CLIMATE_PLATFORM_SCHEMA.extend(PLATFORM_SCHEMA_COMMON.schema)


def select_preset_options(options: list[str]) -> dict[str, str]:
    """Return the select option to use for each supported preset."""
    return {
        SELECT_OPTION_TO_PRESET[option]: option
        for option in options
        if option in SELECT_OPTION_TO_PRESET
    }


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry."""
    config = PLATFORM_SCHEMA_COMMON(dict(config_entry.options))

    async_add_entities(
        [
            HEATER_DOMAIN_TO_CLIMATE[split_entity_id(config[CONF_HEATER])[0]](
                hass,
                config[CONF_HEATER],
                config.get(CONF_TEMPERATURE_SENSOR),
                config.get(CONF_POWER_SENSOR),
                config.get(CONF_POWER_THRESHOLD),
                config_entry.entry_id,
            )
        ]
    )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import the YAML configuration into a config entry."""
    import_data = {
        key: config[key]
        for key in (
            CONF_HEATER,
            CONF_TEMPERATURE_SENSOR,
            CONF_POWER_SENSOR,
            CONF_POWER_THRESHOLD,
            CONF_NAME,
        )
        if key in config
    }
    import_data[CONF_UNIQUE_ID] = config.get(
        CONF_UNIQUE_ID, f"climate_wire_pilot_{config[CONF_HEATER]}"
    )
    hass.async_create_task(_async_import_yaml(hass, import_data))


async def _async_import_yaml(hass: HomeAssistant, import_data: ConfigType) -> None:
    await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
    )
    ir.async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )


class ClimateWirePilotClimate(ClimateEntity):
    """Representation of a Climate Wire Pilot device."""

    _attr_should_poll = False
    _attr_translation_key: str = "climate_wire_pilot"
    _attr_name = None
    _attr_preset_modes = [
        PRESET_COMFORT,
        PRESET_COMFORT_1,
        PRESET_COMFORT_2,
        PRESET_ECO,
        PRESET_AWAY,
        PRESET_NONE,
    ]
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hass: HomeAssistant,
        heater_entity_id: str,
        temperature_sensor_entity_id: str | None,
        power_sensor_entity_id: str | None,
        power_threshold: float | None,
        unique_id: str,
    ) -> None:
        """Initialize the climate device."""

        registry = er.async_get(hass)
        heater_entity = registry.async_get(heater_entity_id)
        has_entity_name = heater_entity.has_entity_name if heater_entity else False

        self.device_entry = async_entity_id_to_device(hass, heater_entity_id)

        self.heater_entity_id = heater_entity_id
        self.temperature_sensor_entity_id = temperature_sensor_entity_id
        self.power_sensor_entity_id = power_sensor_entity_id
        self.power_threshold = power_threshold
        self._cur_temperature = None
        self._cur_power = None

        self._attr_has_entity_name = has_entity_name
        self._attr_unique_id = unique_id

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listener
        if self.temperature_sensor_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self.temperature_sensor_entity_id], self._async_sensor_changed
                )
            )

        if self.power_sensor_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self.power_sensor_entity_id], self._async_power_sensor_changed
                )
            )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.heater_entity_id], self._async_heater_changed
            )
        )

        @callback
        def _async_startup(_: Event | None = None) -> None:
            """Init on startup."""
            if self.temperature_sensor_entity_id is not None:
                sensor_state = self.hass.states.get(self.temperature_sensor_entity_id)
                if sensor_state and sensor_state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                ):
                    self._async_update_temp(sensor_state)
                    self.async_write_ha_state()

            if self.power_sensor_entity_id is not None:
                power_sensor_state = self.hass.states.get(self.power_sensor_entity_id)
                if power_sensor_state and power_sensor_state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                ):
                    self._async_update_power(power_sensor_state)
                    self.async_write_ha_state()

        if self.hass.state is CoreState.running:
            _async_startup()
        else:
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

    # Temperature
    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the sensor temperature."""
        return self._cur_temperature

    @property
    def available(self) -> bool:
        """Return if the heater is available."""
        state = self.hass.states.get(self.heater_entity_id)
        return state is not None and state.state not in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        )

    # Presets
    @property
    def preset_mode(self) -> str | None:
        """Preset current mode."""
        state = self.hass.states.get(self.heater_entity_id)
        if state is None:
            return None

        return self._heater_state_to_preset(state)

    def _heater_state_to_preset(self, state: State) -> str | None:
        raise NotImplementedError

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        if preset_mode not in self.preset_modes:
            _LOGGER.error("Unknown preset mode '%s'", preset_mode)
            return

        await self._async_set_heater_preset(preset_mode)

    # Modes
    @property
    def hvac_modes(self) -> list[HVACMode]:
        """List of available operation modes."""
        return [HVACMode.HEAT, HVACMode.OFF]

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            preset = PRESET_COMFORT
        elif hvac_mode == HVACMode.OFF:
            preset = PRESET_NONE
        else:
            _LOGGER.error("Unknown HVAC mode '%s'", hvac_mode)
            return

        await self._async_set_heater_preset(preset)

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, off mode."""
        preset = self.preset_mode
        if preset is None:
            return None
        if preset == PRESET_NONE:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self.power_threshold is None or self._cur_power is None:
            return None
        if self._cur_power > self.power_threshold:
            return HVACAction.HEATING
        return HVACAction.IDLE

    async def _async_sensor_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle temperature changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_temp(new_state)
        self.async_write_ha_state()

    async def _async_power_sensor_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle power sensor changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_power(new_state)
        self.async_write_ha_state()

    @callback
    def _async_heater_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle heater switch state changes."""
        new_state = event.data["new_state"]
        if new_state is None:
            return
        self.async_write_ha_state()

    @callback
    def _async_update_temp(self, state: State):
        try:
            cur_temp = float(state.state)
            if not math.isfinite(cur_temp):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._cur_temperature = cur_temp
        except ValueError as ex:
            _LOGGER.error("Unable to update from temperature sensor: %s", ex)

    @callback
    def _async_update_power(self, state: State):
        try:
            cur_power = float(state.state)
            if not math.isfinite(cur_power):
                raise ValueError(f"Power sensor has illegal state {state.state}")
            self._cur_power = cur_power
        except ValueError as ex:
            _LOGGER.error("Unable to update from power sensor: %s", ex)

    async def _async_set_heater_preset(self, preset: str) -> None:
        raise NotImplementedError


class LightWirePilotClimate(ClimateWirePilotClimate):
    """Wire pilot thermostat controlled by the brightness of a light."""

    def _heater_state_to_preset(self, state: State) -> str:
        brightness = state.attributes.get(ATTR_BRIGHTNESS)
        value = 0 if brightness is None else round(brightness / 255 * 99)

        for max_value, preset in LIGHT_VALUE_TO_PRESET:
            if value <= max_value:
                return preset
        return PRESET_COMFORT

    async def _async_set_heater_preset(self, preset: str) -> None:
        await self.hass.services.async_call(
            LIGHT_DOMAIN,
            LIGHT_SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: self.heater_entity_id,
                ATTR_BRIGHTNESS: PRESET_TO_LIGHT_VALUE[preset] * 255 / 99,
            },
        )


class SelectWirePilotClimate(ClimateWirePilotClimate):
    """Wire pilot thermostat controlled by the option of a select."""

    def _heater_state_to_preset(self, state: State) -> str | None:
        return SELECT_OPTION_TO_PRESET.get(state.state)

    async def _async_set_heater_preset(self, preset: str) -> None:
        state = self.hass.states.get(self.heater_entity_id)
        options = state.attributes.get(ATTR_OPTIONS, []) if state else []
        option = select_preset_options(options).get(preset)
        if option is None:
            _LOGGER.error(
                "No option for preset '%s' on entity %s",
                preset,
                self.heater_entity_id,
            )
            return

        await self.hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: self.heater_entity_id, ATTR_OPTION: option},
        )


HEATER_DOMAIN_TO_CLIMATE: dict[str, type[ClimateWirePilotClimate]] = {
    LIGHT_DOMAIN: LightWirePilotClimate,
    SELECT_DOMAIN: SelectWirePilotClimate,
}
