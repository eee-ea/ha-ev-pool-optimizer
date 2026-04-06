# HA Energy Optimizer

Minimizes electricity cost for a residential setup by scheduling a pool heat pump and an EV charger based on Nord Pool spot prices, solar generation forecasts, and real-time solar export.

## How it works

Devices are allowed to run when **at least one** of these conditions is true:

| Condition | Pool | EV |
|---|:---:|:---:|
| Solar surplus covers minimum power | ✓ | ✓ |
| Current hour is among cheapest N of the day AND price below threshold | ✓ | ✓ |
| Night window (23:00–07:00) AND price below night limit | | ✓ |

Once started, a minimum runtime timer prevents rapid on/off cycling (20 min pool, 30 min EV). When solar triggers EV charging, the charge current is adjusted dynamically every 2 minutes to follow available export power.

All negative Nord Pool price hours are automatically included in the cheapest-hours selection regardless of the `cheap_quarters_per_day` count.

### Smart night charging

Within the 23:00–07:00 window the charge current is re-evaluated every 15 minutes:

- The optimizer looks at all remaining night quarters and finds the cheapest one ahead.
- If the current quarter costs more than 10 % above that cheapest future quarter, it throttles to the *guarantee current* — the minimum amps needed so the car still reaches the target range by 07:00 assuming all remaining quarters run at that current.
- Otherwise it charges at maximum current — no saving is worth deferring.
- When fewer than 3 quarters remain before 07:00 it always charges at maximum (urgency override).

A **Force charge next night** toggle bypasses the price gate entirely — the night window opens at 23:00 regardless of spot price — while still applying the price-optimised current schedule within the window. The toggle clears automatically at 07:00 or when the target range is reached.

## Files

| File | Purpose |
|---|---|
| `energy_optimizer_package.yaml` | All logic: sensors, automations, scripts, timers |
| `overview_card.yaml` | Dashboard card for monitoring and manual control |
| `plotly_card.yaml` | 2-week runtime and cost history graph |
| `setup_wizard.py` | Interactive setup wizard — generates configured YAML files |

## Quick start

```bash
python setup_wizard.py
```

The wizard asks for your entity names and configuration values, then writes ready-to-use YAML files to a directory of your choice. Requires Python 3.6+, no additional packages needed.

> **Tip:** Running the wizard is the recommended way to set up all entities. It covers every `PLACEHOLDER_*` value in the YAML files and validates your Nord Pool area code and config entry ID step by step.

## Prerequisites

### Integrations

| Integration | Provides | Used for |
|---|---|---|
| [Nord Pool](https://www.home-assistant.io/integrations/nordpool/) | `sensor.nord_pool_<AREA>_current_price` | Spot price, cheapest-hours selection |
| Grid/smart meter (e.g. [DSMR](https://www.home-assistant.io/integrations/dsmr/), Shelly EM, P1) | Grid export sensor, grid import sensor | Solar surplus detection and dynamic amp control |
| [Forecast.Solar](https://www.home-assistant.io/integrations/forecast_solar/) or similar | Remaining solar production today (kWh) | EV solar-budget assessment |
| [Easee](https://github.com/fondberg/easee_hass) (HACS) | Charger switch, charging amps number | EV charger control |
| EV integration (Tesla, Kia, BMW, …) | Plugged-in binary sensor, range sensor | Car connected state and range |
| Pool temperature sensor | Temperature in °C | Pool heat need |
| Pool switch (Shelly, Sonoff, …) | Switch entity | Pool heat pump control |

### Custom frontend cards (HACS)

| Card | Used in |
|---|---|
| [plotly-graph](https://github.com/dbuezas/lovelace-plotly-graph-card) | `plotly_card.yaml` |
| [layout-card](https://github.com/thomasloven/lovelace-layout-card) | `overview_card.yaml` (responsive columns) |

## Manual installation (without wizard)

1. Open `energy_optimizer_package.yaml`, `overview_card.yaml`, and `plotly_card.yaml`.
2. Find every `PLACEHOLDER_*` string and replace it with your actual value.  
   The full list of placeholders and what they represent is shown in the wizard or in the table below.
3. Follow the installation steps in the next section.

### Placeholder reference

| Placeholder | What to put here |
|---|---|
| `PLACEHOLDER_NORDPOOL_AREA` | Your Nord Pool price area (e.g. `SE4`, `FI`, `DK1`) |
| `PLACEHOLDER_NORDPOOL_CONFIG_ENTRY` | Nord Pool config entry ID — see [how to find it](#finding-ids) |
| `PLACEHOLDER_CURRENCY` | Currency code (e.g. `SEK`, `EUR`, `DKK`) |
| `PLACEHOLDER_PRICE_VAT` | VAT multiplier (e.g. `1.25` for 25% VAT) |
| `PLACEHOLDER_PRICE_SURCHARGE` | Energy surcharge multiplier (use `1.0` if none) |
| `PLACEHOLDER_GRID_FEE` | Fixed grid fee per kWh (e.g. `0.90`) |
| `PLACEHOLDER_EV_CHARGER_SWITCH` | `switch.your_charger_enabled` |
| `PLACEHOLDER_EV_CHARGING_AMPS` | `number.your_charging_amps` |
| `PLACEHOLDER_EASEE_DEVICE_ID` | Easee device ID hex string — see [how to find it](#finding-ids) |
| `PLACEHOLDER_EV_PLUGGED_IN` | `binary_sensor.your_car_connected` |
| `PLACEHOLDER_EV_RANGE` | `sensor.your_car_range` |
| `PLACEHOLDER_POOL_SWITCH` | `switch.your_pool_heat_pump` |
| `PLACEHOLDER_POOL_TEMPERATURE` | `sensor.your_pool_temperature` |
| `PLACEHOLDER_GRID_EXPORT` | `sensor.your_grid_export_kw` |
| `PLACEHOLDER_GRID_IMPORT` | `sensor.your_grid_import_kw` |
| `PLACEHOLDER_SOLAR_FORECAST` | `sensor.your_solar_forecast_remaining_today` |

## Installation

1. Run `python setup_wizard.py` (or manually replace placeholders — see above).
2. Copy `energy_optimizer_package.yaml` to your HA packages folder and enable packages in `configuration.yaml`:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages/
   ```
3. Add the two dashboard cards via the Lovelace UI (raw config editor) or include the YAML files in your dashboard config.
4. Restart Home Assistant.

## Configuration

All settings are exposed as `input_number` / `input_boolean` helpers and can be adjusted from the dashboard without restarting HA.

### Master switch

| Entity | Default | Description |
|---|---|---|
| `input_boolean.energy_optimization_enabled` | on | Disables all automations when off |

### Pool

| Entity | Default | Description |
|---|---|---|
| `input_number.pool_target_temp` | 28 °C | Heat pump runs until pool reaches this temperature |
| `input_number.pool_hp_power_kw` | 1.8 kW | Rated power of the heat pump (used for solar surplus check and cost calculation) |
| `input_number.max_grid_price_pool` | 1.00 | Maximum actual price at which grid charging is allowed |

### EV

| Entity | Default | Description |
|---|---|---|
| `input_number.ev_target_range_km` | 420 km | Charger runs until this range is reached |
| `input_number.ev_charge_current_a` | 16 A | Maximum charge current |
| `input_number.ev_charge_phases` | 3 | Number of phases |
| `input_number.ev_solar_min_amps` | 6 A | Minimum current to start solar charging; dynamic control ramps between this and 15 A |
| `input_number.max_grid_price_ev` | 0.70 | Maximum actual price at which grid charging is allowed |
| `input_number.ev_night_price_limit` | 0.70 | Night window (23:00–07:00) price ceiling; bypassed when Force charge is on |
| `input_boolean.force_charge_next_night` | off | Forces the night window open regardless of price; applies price-optimised current schedule within the window |

### Pricing

| Entity | Default | Description |
|---|---|---|
| `input_number.cheap_quarters_per_day` | 12 | How many of the cheapest hourly slots to enable per day |

## Price formula

```
actual_price = spot_price × VAT_MULTIPLIER × SURCHARGE + GRID_FEE
```

The constants are set during wizard setup (or by replacing the `PLACEHOLDER_PRICE_*` values manually). Update them in `sensor.actual_electricity_price` to match your tariff.

## Key sensors

### Decision chain — EV

```
EV_PLUGGED_IN ON + range < target  →  ev_needs_charge
  + (solar_export ≥ ev_solar_min_amps × phases × 230 V)  →  solar_surplus_for_ev_now
  + (NOT force_charge_next_night
     AND current hour in cheapest N AND price ≤ threshold)→  cheap quarter path
  + (23:00–07:00 AND (price ≤ night limit OR force_charge))→  night window path
  →  ev_should_charge_now  →  automation starts charger

Night window current (re-evaluated every 15 min):
  current_price > 1.10 × cheapest_remaining → guarantee_amps (throttle)
  else                                       → max amps
  quarters_remaining ≤ 3                    → max amps (urgency override)
```

### Decision chain — Pool

```
pool_temp < target  →  pool_needs_heat
  + (solar_export ≥ pool_hp_power_kw)                     →  solar_surplus_for_pool_now
  + (current hour in cheapest N AND price ≤ threshold)    →  cheap quarter path
  →  pool_should_run_now  →  automation turns on switch
```

## Dynamic EV charging current

When solar triggers charging, `PLACEHOLDER_EV_CHARGING_AMPS` starts at `ev_solar_min_amps` and is adjusted every 2 minutes:

- Grid export > 0.5 kW → increase by 1 A (max 15 A)
- Grid import > 0.3 kW → decrease by 1 A (min 5 A)

When charging stops, current is reset to `ev_charge_current_a`. When grid-price or night-window triggers charging, current starts at the full `ev_charge_current_a` and dynamic adjustment is inactive.

## Cost tracking

Four template sensors estimate electricity cost by multiplying runtime × rated power × actual price:

| Sensor | Period |
|---|---|
| `sensor.pool_cost_this_hour` | Current hour (resets at :00) |
| `sensor.ev_cost_this_hour` | Current hour (resets at :00) |
| `sensor.pool_cost_today` | Since midnight |
| `sensor.ev_cost_today` | Since midnight |

Daily cost uses the current spot price as a proxy for the average price across the day — this is an approximation. EV cost is based on `ev_charge_current_a` (rated maximum), not the actual dynamic current.

## Alerts

Persistent notifications appear in the HA dashboard when:
- The EV plugged-in sensor, EV range sensor, grid export sensor, or `sensor.cheapest_quarters_today` become `unavailable` or `unknown`
- `sensor.cheapest_quarters_today` has not updated in more than 2 hours while the optimizer is enabled

## Finding IDs

### Nord Pool config entry ID

1. Go to **Settings → Devices & Services**
2. Find the **Nord Pool** integration and click it
3. Click the three-dot menu (⋮) → **System Information**
4. Copy the value next to `config_entry_id`

### Easee device ID

1. Go to **Settings → Devices & Services**
2. Find the **Easee** integration and click it
3. Click your charger device
4. Click the three-dot menu (⋮) → **System Information**
5. Copy the value next to `device_id`

## Dashboard cards

### overview_card.yaml

Responsive grid (1 column on phone, 2+ on wider screens) containing:

1. **Quick View** — glance card with live on/off states for all key switches and logic sensors
2. **Control** — sliders and toggles for all `input_number` / `input_boolean` settings
3. **Live Status** — current sensor readings (pool temp, EV range, prices, solar export, timers)
4. **Decision Sensors** — all intermediate binary sensors showing the full decision chain
5. **Cheapest Quarters Today** — markdown list of today's cheap hourly slots with prices
6. **Cheapest Quarters Tomorrow** — same for tomorrow (hidden when data is unavailable)
7. **Manual controls** — Start/Stop EV charger and Pool ON/OFF buttons
8. **Night Charging Plan** — conditional table showing per-15-min amps, price, and cost for the coming night window (visible when night window active or Force charge is on; shows "Preview" before 23:00)
9. **History graph** — 24-hour chart of pool temp, EV range, prices, and solar export

### plotly_card.yaml

2-week bar chart with dual y-axes:
- **Left axis** — minutes per hour the pool heat pump and EV charger were running
- **Right axis** — cost per hour and cumulative cost per day for each device

Refreshes every 5 minutes.
