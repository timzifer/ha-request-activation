"""The Request Activation integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TARGET_ENTITIES, CONF_TARGET_ENTITY, PLATFORMS


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry to current version."""
    if entry.version == 1:
        new_options = dict(entry.options)
        old_target = new_options.pop(CONF_TARGET_ENTITY, None)
        new_options[CONF_TARGET_ENTITIES] = [old_target] if old_target else []
        hass.config_entries.async_update_entry(
            entry, options=new_options, version=2
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Request Activation from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
