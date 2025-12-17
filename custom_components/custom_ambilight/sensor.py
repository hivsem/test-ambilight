"""Sensor module for Custom Ambilight integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import color_RGB_to_hs

from .api import avg_rgb, avg_rgb_by_side, avg_rgb_for_side
from .const import DOMAIN


class CustomAmbilightMeasuredColorSensor(CoordinatorEntity, SensorEntity):
    """Expose measured Ambilight color as a sensor."""

    _attr_translation_key = "ambilight_measured_color"
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_measured_color"
        self._device_entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_entry_id)},
            name="Philips Ambilight",
            manufacturer="Philips",
            model="Ambilight",
            sw_version="1.0",
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        if not isinstance(data, dict):
            return None
        rgb = avg_rgb(data)
        if rgb is None:
            return None
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not isinstance(data, dict):
            return {}
        rgb = avg_rgb(data)
        attrs = {}
        if rgb is not None:
            r, g, b = rgb
            hs = color_RGB_to_hs(r, g, b)
            attrs["avg_rgb"] = [r, g, b]
            attrs["avg_hs"] = [round(hs[0], 1), round(hs[1], 1)]
        by_side = avg_rgb_by_side(data)
        if by_side:
            attrs["avg_rgb_by_side"] = {
                side: (list(side_rgb) if side_rgb is not None else None) for side, side_rgb in by_side.items()
            }
        return attrs


class CustomAmbilightMeasuredSideColorSensor(CoordinatorEntity, SensorEntity):
    """Expose measured Ambilight color for one side as a sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, side: str) -> None:
        super().__init__(coordinator)
        self._side = side
        self._attr_unique_id = f"{entry_id}_measured_color_{side}"
        self._device_entry_id = entry_id
        if side == "left":
            self._attr_translation_key = "ambilight_measured_color_left"
        elif side == "right":
            self._attr_translation_key = "ambilight_measured_color_right"
        else:
            self._attr_translation_key = "ambilight_measured_color"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_entry_id)},
            name="Philips Ambilight",
            manufacturer="Philips",
            model="Ambilight",
            sw_version="1.0",
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        if not isinstance(data, dict):
            return None
        rgb = avg_rgb_for_side(data, self._side)
        if rgb is None:
            return None
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not isinstance(data, dict):
            return {}
        rgb = avg_rgb_for_side(data, self._side)
        if rgb is None:
            return {}
        r, g, b = rgb
        hs = color_RGB_to_hs(r, g, b)
        return {
            "avg_rgb": [r, g, b],
            "avg_hs": [round(hs[0], 1), round(hs[1], 1)],
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up Custom Ambilight sensor entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    measured_coordinator = entry_data["measured_coordinator"]
    async_add_entities(
        [
            CustomAmbilightMeasuredColorSensor(measured_coordinator, entry.entry_id),
            CustomAmbilightMeasuredSideColorSensor(measured_coordinator, entry.entry_id, "left"),
            CustomAmbilightMeasuredSideColorSensor(measured_coordinator, entry.entry_id, "right"),
        ],
        update_before_add=True,
    )
