"""HA Energy Optimizer — custom integration.

On first setup (config entry created by the wizard) this integration writes
the three configured YAML files into the HA packages/ directory, then shows
a persistent notification asking the user to restart Home Assistant.

The integration itself does not own any runtime entities; all sensors and
automations come from the written YAML package files after restart.
"""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, TEMPLATE_FILES, PH_NORDPOOL_AREA, PH_NORDPOOL_ENTITY

_LOGGER = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Write configured YAML files and prompt for restart."""
    data = dict(entry.data)
    area = data.get(PH_NORDPOOL_AREA, "")

    packages_dir = Path(hass.config.path("packages"))

    def _write_files() -> list[str]:
        packages_dir.mkdir(exist_ok=True)
        written = []
        for filename in TEMPLATE_FILES:
            src = TEMPLATES_DIR / filename
            if not src.exists():
                _LOGGER.warning("Template not found: %s", src)
                continue

            content = src.read_text(encoding="utf-8")

            # The Nord Pool entity name uses the lowercase area code
            # (e.g. sensor.nord_pool_se4_current_price), but the dict key
            # returned by the Nord Pool API uses the area as-is (e.g. 'SE4').
            # Substitute the entity name first, then all remaining placeholders.
            content = content.replace(
                PH_NORDPOOL_ENTITY,
                f"sensor.nord_pool_{area.lower()}_current_price",
            )
            for key, value in data.items():
                content = content.replace(key, str(value))

            dst = packages_dir / filename
            dst.write_text(content, encoding="utf-8")
            written.append(filename)
            _LOGGER.info("Written: %s", dst)

        return written

    try:
        written = await hass.async_add_executor_job(_write_files)
    except OSError as exc:
        _LOGGER.error("Failed to write package files: %s", exc)
        return False

    packages_path = hass.config.path("packages")
    hass.components.persistent_notification.async_create(
        f"Energy Optimizer files written to `{packages_path}/`:\n\n"
        + "\n".join(f"- `{f}`" for f in written)
        + "\n\n**Restart Home Assistant** to activate all sensors and automations.",
        title="Energy Optimizer — setup complete",
        notification_id="energy_optimizer_setup",
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nothing to unload — entities are owned by the YAML package, not this integration."""
    return True
