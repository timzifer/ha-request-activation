"""Sensor platform for Request Activation."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_REQUEST_ENTITIES


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
        self._unsub_listeners: list[callback] = []

    @property
    def native_value(self) -> int:
        """Return the number of active request entities."""
        request_entities: list[str] = self._entry.options.get(
            CONF_REQUEST_ENTITIES, []
        )
        count = 0
        for entity_id in request_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state == STATE_ON:
                count += 1
        return count

    async def async_added_to_hass(self) -> None:
        """Register state listeners when added to hass."""
        self._subscribe_to_entities()

    def _subscribe_to_entities(self) -> None:
        """Subscribe to state changes of request entities."""
        self._unsubscribe()

        request_entities = list(
            self._entry.options.get(CONF_REQUEST_ENTITIES, [])
        )

        if request_entities:
            self._unsub_listeners.append(
                async_track_state_change_event(
                    self.hass, request_entities, self._async_state_changed
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
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners when removed."""
        self._unsubscribe()
