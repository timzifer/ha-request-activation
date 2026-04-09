"""Binary sensor platform for Request Activation."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_ENABLED_ENTITY, CONF_REQUEST_ENTITIES, CONF_TARGET_ENTITY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor from a config entry."""
    async_add_entities([RequestActivationBinarySensor(entry)])


class RequestActivationBinarySensor(BinarySensorEntity):
    """Binary sensor that combines multiple boolean entities with OR logic."""

    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self._entry = entry
        self._attr_name = f"{entry.data[CONF_NAME]} Active"
        self._attr_unique_id = f"{entry.entry_id}_active"
        self._attr_icon = "mdi:link-variant"
        self._unsub_listeners: list[callback] = []
        self._previous_is_on: bool | None = None

    @property
    def is_on(self) -> bool:
        """Return true if any request entity is on and the group is enabled."""
        options = self._entry.options
        request_entities: list[str] = options.get(CONF_REQUEST_ENTITIES, [])
        enabled_entity: str | None = options.get(CONF_ENABLED_ENTITY)

        # Check enabled state
        if enabled_entity:
            enabled_state = self.hass.states.get(enabled_entity)
            if not enabled_state or enabled_state.state != STATE_ON:
                return False

        # OR logic across all request entities
        for entity_id in request_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state == STATE_ON:
                return True

        return False

    async def async_added_to_hass(self) -> None:
        """Register state listeners when added to hass."""
        self._subscribe_to_entities()
        # Set initial previous state
        self._previous_is_on = self.is_on
        # Sync target entity on startup
        await self._sync_target_entity()

    def _subscribe_to_entities(self) -> None:
        """Subscribe to state changes of all tracked entities."""
        self._unsubscribe()

        options = self._entry.options
        tracked: list[str] = list(options.get(CONF_REQUEST_ENTITIES, []))

        enabled_entity = options.get(CONF_ENABLED_ENTITY)
        if enabled_entity:
            tracked.append(enabled_entity)

        if tracked:
            self._unsub_listeners.append(
                async_track_state_change_event(
                    self.hass, tracked, self._async_state_changed
                )
            )

    def _unsubscribe(self) -> None:
        """Remove all state listeners."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    @callback
    def _async_state_changed(self, event: Event) -> None:
        """Handle state changes of tracked entities."""
        new_is_on = self.is_on
        self.async_write_ha_state()

        if new_is_on != self._previous_is_on:
            self._previous_is_on = new_is_on
            self.hass.async_create_task(self._sync_target_entity())

    async def _sync_target_entity(self) -> None:
        """Turn target entity on/off based on current state."""
        target_entity = self._entry.options.get(CONF_TARGET_ENTITY)
        if not target_entity:
            return

        service = "turn_on" if self.is_on else "turn_off"
        await self.hass.services.async_call(
            "homeassistant",
            service,
            {"entity_id": target_entity},
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners when removed."""
        self._unsubscribe()
