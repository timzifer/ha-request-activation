"""Binary sensor platform for Request Activation."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_ENABLED_ENTITY, CONF_REQUEST_ENTITIES, CONF_TARGET_ENTITY

_IGNORED_STATES = {STATE_UNAVAILABLE, STATE_UNKNOWN}


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
    _attr_icon = "mdi:link-variant"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self._entry = entry
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = f"{entry.entry_id}_active"
        self._previous_is_on: bool | None = None

    @property
    def is_on(self) -> bool | None:
        """Return true if any request entity is on and the group is enabled."""
        options = self._entry.options
        request_entities: list[str] = options.get(CONF_REQUEST_ENTITIES, [])
        enabled_entity: str | None = options.get(CONF_ENABLED_ENTITY)

        # Check enabled state
        if enabled_entity:
            enabled_state = self.hass.states.get(enabled_entity)
            if enabled_state is None or enabled_state.state in _IGNORED_STATES:
                return None
            if enabled_state.state != STATE_ON:
                return False

        # OR logic across all request entities
        any_on = False
        all_unknown = True
        for entity_id in request_entities:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in _IGNORED_STATES:
                all_unknown = False
                if state.state == STATE_ON:
                    any_on = True
                    break

        if all_unknown and request_entities:
            return None
        return any_on

    @property
    def extra_state_attributes(self) -> dict[str, list[str] | int]:
        """Return extra attributes showing active request sources."""
        request_entities: list[str] = self._entry.options.get(
            CONF_REQUEST_ENTITIES, []
        )
        active = [
            eid
            for eid in request_entities
            if (s := self.hass.states.get(eid)) and s.state == STATE_ON
        ]
        return {
            "active_requests": active,
            "total_requests": len(request_entities),
        }

    async def async_added_to_hass(self) -> None:
        """Register state listeners when added to hass."""
        tracked: list[str] = list(
            self._entry.options.get(CONF_REQUEST_ENTITIES, [])
        )
        enabled_entity = self._entry.options.get(CONF_ENABLED_ENTITY)
        if enabled_entity:
            tracked.append(enabled_entity)

        if tracked:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, tracked, self._async_state_changed
                )
            )

        # Set initial previous state and sync target
        self._previous_is_on = self.is_on
        await self._sync_target_entity()

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
