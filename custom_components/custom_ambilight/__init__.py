"""Initialisation module for Custom Ambilight integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import MyApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Custom Ambilight from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API instance with host, connection type, username, and password from the config entry
    api = MyApi(entry.data["host"], entry.data["type"], entry.data.get("username"), entry.data.get("password"))

    # Validate the API connection
    if not await api.validate_connection():
        raise ConfigEntryNotReady

    # Create data update coordinators
    config_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="custom_ambilight_config",
        update_method=api.get_data,
        update_interval=timedelta(seconds=30),
    )

    measured_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="custom_ambilight_measured",
        update_method=api.get_measured,
        update_interval=timedelta(seconds=0.5),
    )

    config_coordinator.api = api
    measured_coordinator.api = api

    # Fetch initial data (config is required; measured is best-effort)
    await config_coordinator.async_refresh()
    await measured_coordinator.async_refresh()

    if not config_coordinator.last_update_success:
        raise ConfigEntryNotReady

    # Store coordinators for platforms to access
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "config_coordinator": config_coordinator,
        "measured_coordinator": measured_coordinator,
    }

    # Forward the entry setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        api = entry_data.get("api")
        if api is not None:
            await api.client.aclose()

    return unload_ok
