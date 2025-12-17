"""Light module for Custom Ambilight integration."""

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import color_RGB_to_hs

from .api import avg_rgb, avg_rgb_by_side
from .const import DOMAIN


class CustomAmbilightLight(CoordinatorEntity, LightEntity):
    """Representation of a Custom Ambilight light."""

    _attr_translation_key = "ambilight"
    _attr_has_entity_name = True

    def __init__(self, coordinator, measured_coordinator, entry_id) -> None:
        """Initialize the Custom Ambilight light."""
        super().__init__(coordinator)
        self.api = coordinator.api
        self._measured_coordinator = measured_coordinator
        self._attr_supported_features = LightEntityFeature.EFFECT
        self._attr_supported_color_modes = {ColorMode.HS}
        self._attr_color_mode = ColorMode.HS
        self._attr_unique_id = entry_id  # Use the config entry ID as the unique ID

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name="Philips Ambilight",
            manufacturer="Philips",
            model="Ambilight",
            sw_version="1.0",
        )

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self.api.get_is_on()

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self.api.get_brightness()

    @property
    def hs_color(self):
        """Return the hue and saturation color value [float, float]."""
        configured = self.api.get_hs_color()
        if configured is not None:
            return configured

        if not self._measured_coordinator or not self._measured_coordinator.last_update_success:
            return None
        measured = self._measured_coordinator.data
        if not isinstance(measured, dict):
            return None
        rgb = avg_rgb(measured)
        if rgb is None:
            return None
        hs = color_RGB_to_hs(*rgb)
        return (round(hs[0], 1), round(hs[1], 1))

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return [effect["friendly_name"] for effect in self.api.EFFECTS.values()]

    @property
    def effect(self):
        """Return the current effect."""
        return self.api.get_effect()

    @property
    def extra_state_attributes(self):
        """Expose measured Ambilight colors as extra attributes."""
        attrs = {}
        if not self._measured_coordinator:
            return attrs
        measured = self._measured_coordinator.data if self._measured_coordinator.last_update_success else None
        if isinstance(measured, dict):
            overall = avg_rgb(measured)
            if overall is not None:
                attrs["ambilight_measured_avg_rgb"] = list(overall)
            by_side = avg_rgb_by_side(measured)
            if by_side:
                attrs["ambilight_measured_avg_rgb_by_side"] = {
                    side: (list(rgb) if rgb is not None else None) for side, rgb in by_side.items()
                }
        return attrs

    async def async_added_to_hass(self) -> None:
        """Register listeners."""
        await super().async_added_to_hass()
        if self._measured_coordinator:
            self.async_on_remove(self._measured_coordinator.async_add_listener(self.async_write_ha_state))

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self.coordinator.async_refresh()
        await self.api.turn_on(**kwargs)
        await self.coordinator.async_refresh()

    async def async_turn_off(self):
        """Turn the light off."""
        await self.coordinator.async_refresh()
        await self.api.turn_off()
        await self.coordinator.async_refresh()


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Custom Ambilight light based on a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["config_coordinator"]
    measured_coordinator = entry_data["measured_coordinator"]
    async_add_entities(
        [CustomAmbilightLight(coordinator, measured_coordinator, entry.entry_id)],
        update_before_add=True,
    )
