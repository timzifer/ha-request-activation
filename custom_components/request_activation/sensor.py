"""Sensor platform for Request Activation."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    EVENT_HOMEASSISTANT_STARTED,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_REQUEST_ENTITIES

_IGNORED_STATES = {STATE_UNAVAILABLE, STATE_UNKNOWN}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor from a config entry."""
    async_add_entities([RequestActivationLevelSensor(entry)])


class RequestActivationLevelSensor(SensorEntity):
    """Sensor that counts how many request entities are currently on."""

    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "requests"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_name = f"{entry.data[CONF_NAME]} Level"
        self._attr_unique_id = f"{entry.entry_id}_level"

    @property
    def native_value(self) -> int | None:
        """Return the number of active request entities."""
        request_entities: list[str] = self._entry.options.get(
            CONF_REQUEST_ENTITIES, []
        )
        count = 0
        all_unknown = True
        for entity_id in request_entities:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in _IGNORED_STATES:
                all_unknown = False
                if state.state == STATE_ON:
                    count += 1

        if all_unknown and request_entities:
            return None
        return count

    async def async_added_to_hass(self) -> None:
        """Register state listeners when added to hass."""
        request_entities = list(
            self._entry.options.get(CONF_REQUEST_ENTITIES, [])
        )

        if request_entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, request_entities, self._async_state_changed
                )
            )

        @callback
        def _async_startup(_event=None):
            """Update state once all entities are available."""
            self.async_write_ha_state()

        if self.hass.is_running:
            _async_startup()
        else:
            self.async_on_remove(
                self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, _async_startup
                )
            )

    @callback
    def _async_state_changed(self, event: Event) -> None:
        """Handle state changes of tracked entities."""
        self.async_write_ha_state()
