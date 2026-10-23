"""Una entità climate per IDU: stato, setpoint, temperatura stanza, on/off e setpoint."""
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "bosch_vrf"
# modeControl: 1=fan, 2=cool, 3=heat. 6=dry esiste ma il VRF non lo supporta, quindi disattivato
MODES = {
    "1": HVACMode.FAN_ONLY,
    "2": HVACMode.COOL,
    "3": HVACMode.HEAT,
    # "6": HVACMode.DRY,  # deumidifica: riattivare se il VRF la supporta
}
CODES = {m: int(c) for c, m in MODES.items()}
FAN_AUTO = 255  # fanSpeedDcControl: 255=auto, altrimenti 1..7
FAN_MODES = ["auto", *map(str, range(1, 8))]


def _on(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "on")


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(IduClimate(coordinator, a) for a in coordinator.data)


class IduClimate(CoordinatorEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.FAN_MODE
    )
    _attr_hvac_modes = [HVACMode.OFF, *MODES.values()]
    _attr_target_temperature_step = 0.5
    _attr_fan_modes = FAN_MODES

    def __init__(self, coordinator, address):
        super().__init__(coordinator)
        self._addr = address
        self._attr_unique_id = f"{DOMAIN}_{address}"
        self._attr_name = self._d.get("roomName") or f"IDU {address}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, str(address))}, name=self._attr_name, manufacturer="Bosch")

    @property
    def _d(self) -> dict:
        return self.coordinator.data[self._addr]

    @property
    def hvac_mode(self):
        if not _on(self._d.get("iduPowerOnControl")):
            return HVACMode.OFF
        return MODES.get(str(self._d.get("modeControl")))

    @property
    def target_temperature(self):
        return self._d.get("temperatureSettingControl")

    @property
    def current_temperature(self):
        return self._d.get("roomTemperature")

    @property
    def fan_mode(self):
        v = self._d.get("fanSpeedDcControl")
        return "auto" if v == FAN_AUTO else str(v)

    @property
    def min_temp(self):
        return self._d.get("temperatureLimitCoolingControl", 17)

    @property
    def max_temp(self):
        return self._d.get("temperatureLimitHeatingControl", 30)

    @property
    def extra_state_attributes(self):
        d = self._d
        return {k: d.get(k) for k in ("modeControl", "fanSpeedDcControl", "malfunctionControl", "T2A", "T2B")}

    async def _set(self, prop, value):
        await self.hass.async_add_executor_job(
            self.coordinator.acc.set_property, self._d["uri"], prop, value
        )

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self._set("iduPowerOnControl", 0)
        elif hvac_mode in CODES:
            await self._set("modeControl", CODES[hvac_mode])
            await self._set("iduPowerOnControl", 1)
        else:
            raise HomeAssistantError("Modalità non ancora supportata")
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode):
        await self._set("fanSpeedDcControl", FAN_AUTO if fan_mode == "auto" else int(fan_mode))
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        if (t := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._set("temperatureSettingControl", f"{t:g}")  # l'ACC vuole una stringa
            await self.coordinator.async_request_refresh()
