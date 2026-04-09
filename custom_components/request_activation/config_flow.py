"""Config flow for Request Activation integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
)

from .const import (
    CONF_ENABLED_ENTITY,
    CONF_REQUEST_ENTITIES,
    CONF_TARGET_ENTITIES,
    DOMAIN,
)


def _entities_schema(
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    """Build the entity selection schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_REQUEST_ENTITIES,
                default=defaults.get(CONF_REQUEST_ENTITIES, []),
            ): EntitySelector(
                EntitySelectorConfig(
                    domain=["input_boolean", "binary_sensor", "switch"],
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_ENABLED_ENTITY,
                description={"suggested_value": defaults.get(CONF_ENABLED_ENTITY)},
            ): EntitySelector(
                EntitySelectorConfig(
                    domain=["input_boolean", "binary_sensor", "switch"],
                )
            ),
            vol.Optional(
                CONF_TARGET_ENTITIES,
                default=defaults.get(CONF_TARGET_ENTITIES, []),
            ): EntitySelector(
                EntitySelectorConfig(
                    domain=["switch", "light", "input_boolean", "fan"],
                    multiple=True,
                )
            ),
        }
    )


class RequestActivationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Request Activation."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._name: str = ""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> RequestActivationOptionsFlow:
        """Get the options flow handler."""
        return RequestActivationOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: name input."""
        if user_input is not None:
            self._name = user_input[CONF_NAME]
            return await self.async_step_entities()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): TextSelector(),
                }
            ),
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the entity selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_REQUEST_ENTITIES):
                errors["base"] = "no_request_entities"
            else:
                return self.async_create_entry(
                    title=self._name,
                    data={CONF_NAME: self._name},
                    options={
                        CONF_REQUEST_ENTITIES: user_input[CONF_REQUEST_ENTITIES],
                        CONF_ENABLED_ENTITY: user_input.get(CONF_ENABLED_ENTITY),
                        CONF_TARGET_ENTITIES: user_input.get(CONF_TARGET_ENTITIES, []),
                    },
                )

        return self.async_show_form(
            step_id="entities",
            data_schema=_entities_schema(),
            errors=errors,
        )


class RequestActivationOptionsFlow(OptionsFlowWithReload):
    """Handle options flow for Request Activation."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_REQUEST_ENTITIES):
                errors["base"] = "no_request_entities"
            else:
                return self.async_create_entry(
                    data={
                        CONF_REQUEST_ENTITIES: user_input[CONF_REQUEST_ENTITIES],
                        CONF_ENABLED_ENTITY: user_input.get(CONF_ENABLED_ENTITY),
                        CONF_TARGET_ENTITIES: user_input.get(CONF_TARGET_ENTITIES, []),
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_entities_schema(dict(self.config_entry.options)),
            errors=errors,
        )
