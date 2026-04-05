#!/usr/bin/env python3
"""
HA Energy Optimizer — interactive setup wizard.

Asks for your Home Assistant entity names and configuration, then writes
configured versions of the three YAML files ready to copy into HA.
"""

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

TEMPLATE_FILES = [
    "energy_optimizer_package.yaml",
    "overview_card.yaml",
    "plotly_card.yaml",
]

# ---------------------------------------------------------------------------
# Placeholder definitions
# Each entry: placeholder_key -> (section, label, default, hint)
# ---------------------------------------------------------------------------
FIELDS = [
    # ── Nord Pool ──────────────────────────────────────────────────────────
    ("NORDPOOL", "PLACEHOLDER_NORDPOOL_AREA",
     "Nord Pool price area code",
     "SE4",
     "Examples: SE1 SE2 SE3 SE4  FI  DK1 DK2  NO1 NO2 NO3 NO4 NO5  EE LT LV\n"
     "  Check your Nord Pool integration card in HA for the area it is configured with."),

    ("NORDPOOL", "PLACEHOLDER_NORDPOOL_CONFIG_ENTRY",
     "Nord Pool config entry ID",
     None,
     "Find it in HA:\n"
     "  Settings → Devices & Services → Nord Pool → ⋮ (three dots) → System Information\n"
     "  Copy the value next to 'config_entry_id' (looks like: 01ABC123XYZ...)."),

    # ── Pricing ────────────────────────────────────────────────────────────
    ("PRICING", "PLACEHOLDER_CURRENCY",
     "Currency code",
     "SEK",
     "Examples: SEK  EUR  DKK  NOK  GBP"),

    ("PRICING", "PLACEHOLDER_PRICE_VAT",
     "VAT multiplier",
     "1.25",
     "Swedish VAT is 25% → 1.25.  Use 1.0 if prices from Nord Pool already include VAT."),

    ("PRICING", "PLACEHOLDER_PRICE_SURCHARGE",
     "Energy surcharge multiplier",
     "1.0561",
     "Carrier-specific markup applied on top of VAT.  Use 1.0 if none."),

    ("PRICING", "PLACEHOLDER_GRID_FEE",
     "Fixed grid fee (currency/kWh)",
     "0.90",
     "The flat per-kWh network tariff added on top of the spot price."),

    # ── EV Charger (Easee) ─────────────────────────────────────────────────
    ("EV CHARGER", "PLACEHOLDER_EV_CHARGER_SWITCH",
     "Charger enabled switch entity",
     None,
     "The switch that enables/disables the charger.  Domain must be 'switch'.\n"
     "  Example: switch.my_easee_charger_enabled"),

    ("EV CHARGER", "PLACEHOLDER_EV_CHARGING_AMPS",
     "Charging amps number entity",
     None,
     "The number entity controlling charge current.  Domain must be 'number'.\n"
     "  Example: number.my_charging_amps"),

    ("EV CHARGER", "PLACEHOLDER_EASEE_DEVICE_ID",
     "Easee device ID (hex string)",
     None,
     "Find it in HA:\n"
     "  Settings → Devices & Services → Easee → your charger → ⋮ → System Information\n"
     "  Copy the value next to 'device_id' (looks like: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4)."),

    # ── EV 1 / Primary car ────────────────────────────────────────────────
    ("EV / CARS", "PLACEHOLDER_EV_PLUGGED_IN",
     "EV 1 plugged-in binary sensor",
     None,
     "Reports 'on' when EV 1 is connected to the charger.  Domain: 'binary_sensor'.\n"
     "  Example: binary_sensor.my_car_charger\n"
     "  EV 1 takes priority when both cars are plugged in."),

    ("EV / CARS", "PLACEHOLDER_EV_CHARGING",
     "EV 1 actively charging binary sensor",
     None,
     "Reports 'on' while EV 1 is actively accepting current (goes OFF when the car\n"
     "  reaches its own internal charge limit).  Domain: 'binary_sensor'.\n"
     "  Easee example: binary_sensor.my_car_charging"),

    ("EV / CARS", "PLACEHOLDER_EV_WAKE_BUTTON",
     "EV 1 force data update button",
     None,
     "Pressed just before charging starts to wake a sleeping car.  Domain: 'button'.\n"
     "  Tesla integration example: button.my_car_force_data_update"),

    ("EV / CARS", "PLACEHOLDER_EV_RANGE",
     "EV 1 range sensor",
     None,
     "Current driving range of EV 1 in km.  Domain: 'sensor'.\n"
     "  Example: sensor.my_car_range"),

    # ── EV 2 / Secondary car ──────────────────────────────────────────────
    ("EV / CARS", "PLACEHOLDER_EV2_PLUGGED_IN",
     "EV 2 plugged-in binary sensor",
     None,
     "Reports 'on' when EV 2 is connected to the charger.  Domain: 'binary_sensor'.\n"
     "  Example: binary_sensor.my_second_car_charger"),

    ("EV / CARS", "PLACEHOLDER_EV2_CHARGING",
     "EV 2 actively charging binary sensor",
     None,
     "Reports 'on' while EV 2 is actively accepting current (goes OFF when the car\n"
     "  reaches its own internal charge limit).  Domain: 'binary_sensor'.\n"
     "  Easee example: binary_sensor.my_second_car_charging"),

    ("EV / CARS", "PLACEHOLDER_EV2_WAKE_BUTTON",
     "EV 2 force data update button",
     None,
     "Pressed just before charging starts to wake a sleeping car.  Domain: 'button'.\n"
     "  Tesla integration example: button.my_second_car_force_data_update"),

    ("EV / CARS", "PLACEHOLDER_EV2_RANGE",
     "EV 2 range sensor",
     None,
     "Current driving range of EV 2 in km.  Domain: 'sensor'.\n"
     "  Example: sensor.my_second_car_range"),

    ("EV / CARS", "PLACEHOLDER_EV2_CHARGING_AMPS",
     "EV 2 charging amps number entity",
     None,
     "Controls the charging current for EV 2.  Domain: 'number'.\n"
     "  Example: number.my_second_car_charging_amps\n"
     "  Some chargers expose separate amp entities per charging port."),

    # ── Pool heat pump ─────────────────────────────────────────────────────
    ("POOL HEAT PUMP", "PLACEHOLDER_POOL_SWITCH",
     "Pool heat pump switch entity",
     None,
     "The switch that turns the pool heat pump on/off.  Domain: 'switch'.\n"
     "  Example: switch.pool_heat_pump"),

    ("POOL HEAT PUMP", "PLACEHOLDER_POOL_TEMPERATURE",
     "Pool temperature sensor",
     None,
     "Reports pool water temperature in °C.  Domain: 'sensor'.\n"
     "  Example: sensor.pool_temperature"),

    # ── Grid meter ─────────────────────────────────────────────────────────
    ("GRID METER", "PLACEHOLDER_GRID_EXPORT",
     "Grid export (solar → grid) sensor",
     None,
     "Current power being exported to the grid in kW.  Domain: 'sensor'.\n"
     "  Example: sensor.p1_power_export  (DSMR: sensor.dsmr_reading_electricity_currently_returned)"),

    ("GRID METER", "PLACEHOLDER_GRID_IMPORT",
     "Grid import (grid → home) sensor",
     None,
     "Current power being imported from the grid in kW.  Domain: 'sensor'.\n"
     "  Example: sensor.p1_power_import  (DSMR: sensor.dsmr_reading_electricity_currently_delivered)"),

    # ── Solar forecast ─────────────────────────────────────────────────────
    ("SOLAR FORECAST", "PLACEHOLDER_SOLAR_FORECAST",
     "Remaining solar production today sensor",
     None,
     "Forecasted remaining solar yield today in kWh.  Domain: 'sensor'.\n"
     "  Example: sensor.solar_forecast_remaining  (Forecast.Solar: sensor.energy_production_today_remaining_3)"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ENTITY_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")

EXPECTED_DOMAINS = {
    "PLACEHOLDER_EV_CHARGER_SWITCH": "switch",
    "PLACEHOLDER_EV_CHARGING_AMPS": "number",
    "PLACEHOLDER_EV_PLUGGED_IN": "binary_sensor",
    "PLACEHOLDER_EV_RANGE": "sensor",
    "PLACEHOLDER_EV2_PLUGGED_IN": "binary_sensor",
    "PLACEHOLDER_EV2_CHARGING": "binary_sensor",
    "PLACEHOLDER_EV2_WAKE_BUTTON": "button",
    "PLACEHOLDER_EV2_RANGE": "sensor",
    "PLACEHOLDER_EV2_CHARGING_AMPS": "number",
    "PLACEHOLDER_EV_CHARGING": "binary_sensor",
    "PLACEHOLDER_EV_WAKE_BUTTON": "button",
    "PLACEHOLDER_POOL_SWITCH": "switch",
    "PLACEHOLDER_POOL_TEMPERATURE": "sensor",
    "PLACEHOLDER_GRID_EXPORT": "sensor",
    "PLACEHOLDER_GRID_IMPORT": "sensor",
    "PLACEHOLDER_SOLAR_FORECAST": "sensor",
}


def hr(char="─", width=60):
    print(char * width)


def section_header(title):
    print()
    hr("━")
    print(f"  {title}")
    hr("━")


def ask(key, label, default, hint):
    """Prompt the user for a value.  Returns the entered string."""
    if hint:
        for line in hint.splitlines():
            print(f"  {line}")

    prompt = f"  {label}"
    if default:
        prompt += f"  [{default}]"
    prompt += ": "

    while True:
        raw = input(prompt).strip()
        value = raw if raw else (default or "")

        if not value:
            print("  ✗ This field is required.")
            continue

        # Validate entity IDs
        if key in EXPECTED_DOMAINS:
            if not ENTITY_RE.match(value):
                print(f"  ✗ Must look like 'domain.entity_name' (lowercase, no spaces).")
                continue
            domain = value.split(".")[0]
            expected = EXPECTED_DOMAINS[key]
            if domain != expected:
                print(f"  ✗ Expected domain '{expected}', got '{domain}'.")
                yn = input("     Use it anyway? [y/N]: ").strip().lower()
                if yn != "y":
                    continue

        return value


def confirm_overwrite(path):
    ans = input(f"  '{path.name}' already exists. Overwrite? [y/N]: ").strip().lower()
    return ans == "y"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    hr("═")
    print("  HA Energy Optimizer — Setup Wizard")
    hr("═")
    print()
    print("  This wizard generates configured YAML files for your Home Assistant")
    print("  setup.  You will need the following integrations already installed:")
    print()
    print("    • Nord Pool          (HA core integration)")
    print("    • Easee              (HACS)")
    print("    • A grid/smart meter (e.g. DSMR, P1, Shelly EM, ...)")
    print("    • Forecast.Solar or similar  (for solar forecast)")
    print("    • Your EV integration        (Tesla, Kia, BMW, ...)")
    print("    • Pool temperature sensor    (any sensor reporting °C)")
    print("    • Pool switch                (any switch controlling the heat pump)")
    print()
    print("  Press Enter to keep the value shown in [brackets], or type your own.")

    values = {}
    current_section = None

    for section, key, label, default, hint in FIELDS:
        if section != current_section:
            section_header(section)
            current_section = section
        else:
            print()

        values[key] = ask(key, label, default, hint)

    # ── Ask for output directory ───────────────────────────────────────────
    section_header("OUTPUT")
    print()
    raw_out = input("  Write configured files to directory  [.]: ").strip()
    out_dir = Path(raw_out) if raw_out else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Substitute and write ───────────────────────────────────────────────
    print()
    hr()
    errors = []
    area = values["PLACEHOLDER_NORDPOOL_AREA"]

    for filename in TEMPLATE_FILES:
        src = SCRIPT_DIR / filename
        if not src.exists():
            print(f"  ✗ Template not found: {src}")
            errors.append(filename)
            continue

        content = src.read_text(encoding="utf-8")

        # The Nord Pool entity name uses the lowercase area code
        # (e.g. sensor.nord_pool_se4_current_price), but the API dict key
        # and 'areas:' field use the area as-is (e.g. SE4).
        # Substitute the entity name first, then all remaining placeholders.
        content = content.replace(
            "sensor.nord_pool_PLACEHOLDER_NORDPOOL_AREA_current_price",
            f"sensor.nord_pool_{area.lower()}_current_price",
        )
        for key, val in values.items():
            content = content.replace(key, val)

        # Check for any remaining placeholders
        remaining = re.findall(r"PLACEHOLDER_\w+", content)
        if remaining:
            unique = sorted(set(remaining))
            print(f"  ⚠  {filename}: unreplaced placeholders: {', '.join(unique)}")

        dst = out_dir / filename
        if dst.exists() and dst.resolve() != src.resolve():
            if not confirm_overwrite(dst):
                print(f"  — Skipped {filename}")
                continue

        dst.write_text(content, encoding="utf-8")
        print(f"  ✓ {filename}  →  {dst}")

    print()
    hr("═")
    if errors:
        print("  Done with warnings.  Check messages above.")
    else:
        print("  Done!  Next steps:")
        print()
        print("    1. Copy energy_optimizer_package.yaml to your HA packages/ folder.")
        print("    2. Make sure packages are enabled in configuration.yaml:")
        print("         homeassistant:")
        print("           packages: !include_dir_named packages/")
        print("    3. Add overview_card.yaml and plotly_card.yaml via the")
        print("       Lovelace dashboard raw config editor.")
        print("    4. Restart Home Assistant.")
    hr("═")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
        sys.exit(1)
