# Custom Ambilight
### An integration for Home Assistant

Fork of `aegjoyce/custom-ambilight` with support for reading current Ambilight colors via `GET /6/ambilight/measured`.

Repository: https://github.com/hivsem/test-ambilight


### Why does this exist?
The core PhilipsJS integration is fantastic but has a few issues:
 - The JointSpace API on Philips TVs is fragile and temperamental - it doesn't like having lots of API calls in quick succession and can slow down or crash the TV after a while
 - The Ambilight implementation does not work consistently with all effect types due to various quirks in the JointSpace API

This custom integration fixes the above issues by:
 - Rate-limiting requests to the API and resetting the connection if needed
 - Providing workarounds for Ambilight mode-switching quirks

It also:
 - Enables the use of all Ambilight modes including modes hidden in the TV UI

### How do I install it?
Currently this integration requires:
 - A Philips Ambilight TV running version 6 of the JointSpace API
 - The IP address of your TV
 - A paired username and password for your TV, obtained using [this script](https://github.com/suborb/philips_android_tv/tree/master)

It is also highly recommended to set up the Alexa app and follow the instructions to keep the TV connected even when off.

Install via HACS (custom repository) or copy files manually:

- HACS: add this repository as a custom repository (type: Integration), install, restart Home Assistant.
- Manual: copy `custom_components/custom_ambilight/` into your HA config at `config/custom_components/custom_ambilight/`, then restart Home Assistant.

After restart: `Settings → Devices & services → Add integration → Custom Ambilight`.

If the integration does not appear in the list, check `Settings → System → Logs`. A common reason is missing Python dependencies; this fork declares `httpx` in `custom_components/custom_ambilight/manifest.json` and HA should install it automatically on startup.

### Extras (measured colors)
This fork also exposes the current Ambilight colors from `GET /6/ambilight/measured`:
- Adds a sensor entity: `sensor.<...>_ambilight_measured_color` (state is `#rrggbb`, attributes include average RGB/HS and per-side averages).
- Adds extra attributes on the light entity: `ambilight_measured_avg_rgb` and `ambilight_measured_avg_rgb_by_side`.
 - Light entity reports `hs_color` even while effects are active (derived from measured colors), so it is not `null` in Developer Tools → States.

### Future plans
 - Automatic registration from IP address without having to get a username and password
 - Support for other API versions
