"""Setpoint e temperatura stanza come sensori per ogni IDU."""
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "bosch_vrf"
SENSORS = {"temperatureSettingControl": "Setpoint", "roomTemperature": "Temperatura stanza"}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(IduSensor(coordinator, a, k) for a in coordinator.data for k in SENSORS)


class IduSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, address, key):
        super().__init__(coordinator)
        self._addr, self._key = address, key
        self._attr_name = SENSORS[key]
        self._attr_unique_id = f"{DOMAIN}_{address}_{key}"
        # stesso identifier della climate: i sensori finiscono nello stesso device
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, str(address))})

    @property
    def native_value(self):
        return self.coordinator.data[self._addr].get(self._key)
