"""Bosch VRF ACC: visualizzazione IDU (sola lettura)."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ACC

_LOGGER = logging.getLogger(__name__)
DOMAIN = "bosch_vrf"
PLATFORMS = ["climate", "sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    acc = ACC(entry.data["host"], entry.data["username"], entry.data["password"])

    async def _update():
        try:
            idus = await hass.async_add_executor_job(acc.get_idus)
        except Exception as err:
            raise UpdateFailed(err) from err
        return {i["address"]: i for i in idus}

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=DOMAIN,
        update_method=_update, update_interval=timedelta(seconds=30),
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()
    coordinator.acc = acc
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok
