"""Config flow for Climate Wire Pilot thermostat."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.select import ATTR_OPTIONS, DOMAIN as SELECT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorDeviceClass
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant, State, split_entity_id
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
    wrapped_entity_config_entry_title,
)

from . import CONF_HEATER, DOMAIN
from .climate import (
    CONF_POWER_SENSOR,
    CONF_POWER_THRESHOLD,
    CONF_TEMPERATURE_SENSOR,
    HEATER_DOMAINS,
    PRESET_SELECT_OPTIONS,
    select_preset_options,
)

QUBINO_MANUFACTURER = "Qubino"
QUBINO_PILOT_WIRE_MODEL = "ZMNHJD"

OPTIONS_SCHEMA = {
    vol.Optional(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.TEMPERATURE
        )
    ),
    vol.Optional(CONF_POWER_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.POWER
        )
    ),
    vol.Optional(CONF_POWER_THRESHOLD, default=0): selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=10000,
            unit_of_measurement="W",
            mode=selector.NumberSelectorMode.BOX,
        )
    ),
}


def _is_supported_select(state: State | None) -> bool:
    options = state.attributes.get(ATTR_OPTIONS, []) if state else []
    return len(select_preset_options(options)) == len(PRESET_SELECT_OPTIONS)


def _supported_heaters(hass: HomeAssistant) -> list[str]:
    selects = [
        state.entity_id
        for state in hass.states.async_all(SELECT_DOMAIN)
        if _is_supported_select(state)
    ]
    lights = [
        entity_id
        for entity_id in hass.states.async_entity_ids(LIGHT_DOMAIN)
        if (device := async_entity_id_to_device(hass, entity_id))
        and device.manufacturer == QUBINO_MANUFACTURER
        and device.model == QUBINO_PILOT_WIRE_MODEL
    ]
    return selects + lights


async def get_config_schema(handler: SchemaCommonFlowHandler) -> vol.Schema:
    """Return the config schema, offering only the supported heaters."""
    return vol.Schema(
        {
            vol.Required(CONF_HEATER): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=HEATER_DOMAINS,
                    include_entities=_supported_heaters(handler.parent_handler.hass),
                )
            ),
            **OPTIONS_SCHEMA,
        }
    )


async def validate_heater(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Check that a select heater exposes an option for every preset."""
    heater = user_input[CONF_HEATER]
    if split_entity_id(heater)[0] == SELECT_DOMAIN and not _is_supported_select(
        handler.parent_handler.hass.states.get(heater)
    ):
        raise SchemaFlowError("unsupported_select")
    return user_input


CONFIG_FLOW = {
    "user": SchemaFlowFormStep(get_config_schema, validate_user_input=validate_heater),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(vol.Schema(OPTIONS_SCHEMA)),
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow."""

    MINOR_VERSION = 2

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import a thermostat from YAML."""
        await self.async_set_unique_id(import_data[CONF_UNIQUE_ID])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(data=import_data)

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title and hide the wrapped entity if registered."""
        # Hide the wrapped entry if registered
        registry = er.async_get(self.hass)
        entity_entry = registry.async_get(options[CONF_HEATER])
        if entity_entry is not None and not entity_entry.hidden:
            registry.async_update_entity(
                options[CONF_HEATER], hidden_by=er.RegistryEntryHider.INTEGRATION
            )

        return wrapped_entity_config_entry_title(self.hass, options[CONF_HEATER])
