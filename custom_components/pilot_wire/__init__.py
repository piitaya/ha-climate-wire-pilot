"""Pilot Wire integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, MAJOR_VERSION, MINOR_VERSION, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device import async_entity_id_to_device_id
from homeassistant.helpers.helper_integration import async_handle_source_entity_changes

# Before 2026.8, a device can be shared by several config entries
HAS_SINGLE_CONFIG_ENTRY_DEVICE = (MAJOR_VERSION, MINOR_VERSION) >= (2026, 8)

CONF_HEATER = "heater"
DOMAIN = "pilot_wire"
PLATFORMS = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    if CONF_ENTITY_ID in entry.options:
        _async_adopt_imported_entity(hass, entry)

    def set_heater_entity_id_or_uuid(source_entity_id: str) -> None:
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_HEATER: source_entity_id},
        )

    source_entity_changes_kwargs = (
        {}
        if HAS_SINGLE_CONFIG_ENTRY_DEVICE
        else {"add_helper_config_entry_to_device": False}
    )
    entry.async_on_unload(
        async_handle_source_entity_changes(
            hass,
            helper_config_entry_id=entry.entry_id,
            set_source_entity_id_or_uuid=set_heater_entity_id_or_uuid,
            source_device_id=async_entity_id_to_device_id(
                hass, entry.options[CONF_HEATER]
            ),
            source_entity_id_or_uuid=entry.options[CONF_HEATER],
            **source_entity_changes_kwargs,
        )
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))
    return True


@callback
def _async_adopt_imported_entity(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Move the entity of the imported thermostat to this config entry."""
    options = dict(entry.options)
    entity_id = options.pop(CONF_ENTITY_ID)

    registry = er.async_get(hass)
    if registry.async_get(entity_id):
        registry.async_update_entity_platform(
            entity_id,
            DOMAIN,
            new_config_entry_id=entry.entry_id,
            new_unique_id=entry.entry_id,
        )

    hass.config_entries.async_update_entry(entry, options=options)


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Unhide the heater entity when the thermostat is removed."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get(entry.options[CONF_HEATER])
    if entity_entry and entity_entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
        registry.async_update_entity(entity_entry.entity_id, hidden_by=None)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
