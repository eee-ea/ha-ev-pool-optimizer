"""Config flow — 7-step setup wizard for HA Energy Optimizer."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    PH_NORDPOOL_AREA,
    PH_NORDPOOL_CONFIG_ENTRY,
    PH_CURRENCY,
    PH_PRICE_VAT,
    PH_PRICE_SURCHARGE,
    PH_GRID_FEE,
    PH_EV_CHARGER_SWITCH,
    PH_EV_CHARGING_AMPS,
    PH_EASEE_DEVICE_ID,
    PH_EV_PLUGGED_IN,
    PH_EV_RANGE,
    PH_EV2_PLUGGED_IN,
    PH_EV2_RANGE,
    PH_EV2_CHARGING_AMPS,
    PH_EV_CHARGING,
    PH_EV2_CHARGING,
    PH_EV_WAKE_BUTTON,
    PH_EV2_WAKE_BUTTON,
    PH_POOL_SWITCH,
    PH_POOL_TEMPERATURE,
    PH_GRID_EXPORT,
    PH_GRID_IMPORT,
    PH_SOLAR_FORECAST,
)

# ---------------------------------------------------------------------------
# Step schemas
# ---------------------------------------------------------------------------

STEP_NORDPOOL_SCHEMA = vol.Schema(
    {
        vol.Required(PH_NORDPOOL_CONFIG_ENTRY): selector.ConfigEntrySelector(
            selector.ConfigEntrySelectorConfig(integration="nordpool")
        ),
        vol.Required(PH_NORDPOOL_AREA, default="SE4"): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
    }
)

STEP_PRICING_SCHEMA = vol.Schema(
    {
        vol.Required(PH_CURRENCY, default="SEK"): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
        vol.Required(PH_PRICE_VAT, default=1.25): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1.0, max=2.0, step=0.001, mode="box")
        ),
        vol.Required(PH_PRICE_SURCHARGE, default=1.0561): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1.0, max=2.0, step=0.0001, mode="box")
        ),
        vol.Required(PH_GRID_FEE, default=0.90): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0.0, max=5.0, step=0.01, mode="box")
        ),
    }
)

STEP_EV_CHARGER_SCHEMA = vol.Schema(
    {
        vol.Required(PH_EV_CHARGER_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Required(PH_EV_CHARGING_AMPS): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="number")
        ),
        vol.Required(PH_EASEE_DEVICE_ID): selector.DeviceSelector(
            selector.DeviceSelectorConfig(integration="easee")
        ),
    }
)

STEP_EV_CAR_SCHEMA = vol.Schema(
    {
        vol.Required(PH_EV_PLUGGED_IN): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required(PH_EV_CHARGING): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required(PH_EV_RANGE): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Required(PH_EV_WAKE_BUTTON): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="button")
        ),
        vol.Required(PH_EV2_PLUGGED_IN): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required(PH_EV2_CHARGING): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required(PH_EV2_RANGE): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Required(PH_EV2_WAKE_BUTTON): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="button")
        ),
        vol.Required(PH_EV2_CHARGING_AMPS): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="number")
        ),
    }
)

STEP_POOL_SCHEMA = vol.Schema(
    {
        vol.Required(PH_POOL_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Required(PH_POOL_TEMPERATURE): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
    }
)

STEP_GRID_SOLAR_SCHEMA = vol.Schema(
    {
        vol.Required(PH_GRID_EXPORT): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Required(PH_GRID_IMPORT): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Required(PH_SOLAR_FORECAST): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
    }
)


# ---------------------------------------------------------------------------
# Config flow
# ---------------------------------------------------------------------------

class EnergyOptimizerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the setup wizard."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    # ── Step 1: Nord Pool ──────────────────────────────────────────────────

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_pricing()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_NORDPOOL_SCHEMA,
        )

    # ── Step 2: Pricing ────────────────────────────────────────────────────

    async def async_step_pricing(self, user_input=None):
        if user_input is not None:
            # Store numbers as strings for direct YAML substitution
            self._data[PH_CURRENCY] = user_input[PH_CURRENCY]
            self._data[PH_PRICE_VAT] = str(user_input[PH_PRICE_VAT])
            self._data[PH_PRICE_SURCHARGE] = str(user_input[PH_PRICE_SURCHARGE])
            self._data[PH_GRID_FEE] = str(user_input[PH_GRID_FEE])
            return await self.async_step_ev_charger()

        return self.async_show_form(
            step_id="pricing",
            data_schema=STEP_PRICING_SCHEMA,
        )

    # ── Step 3: EV Charger ─────────────────────────────────────────────────

    async def async_step_ev_charger(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_ev_car()

        return self.async_show_form(
            step_id="ev_charger",
            data_schema=STEP_EV_CHARGER_SCHEMA,
        )

    # ── Step 4: EV / Cars ─────────────────────────────────────────────────

    async def async_step_ev_car(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_pool()

        return self.async_show_form(
            step_id="ev_car",
            data_schema=STEP_EV_CAR_SCHEMA,
        )

    # ── Step 5: Pool ───────────────────────────────────────────────────────

    async def async_step_pool(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_grid_solar()

        return self.async_show_form(
            step_id="pool",
            data_schema=STEP_POOL_SCHEMA,
        )

    # ── Step 6: Grid + Solar (final) ───────────────────────────────────────

    async def async_step_grid_solar(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title="Energy Optimizer",
                data=self._data,
            )

        return self.async_show_form(
            step_id="grid_solar",
            data_schema=STEP_GRID_SOLAR_SCHEMA,
        )
