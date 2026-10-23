"""Allarme e raggiungibilità per ogni IDU."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "bosch_vrf"
# chiave -> (nome, device_class)
SENSORS = {
    "malfunctionControl": ("Allarme", BinarySensorDeviceClass.PROBLEM),
    "status": ("Connessione", BinarySensorDeviceClass.CONNECTIVITY),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(IduBinary(coordinator, a, k) for a in coordinator.data for k in SENSORS)


class IduBinary(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, address, key):
        super().__init__(coordinator)
        self._addr, self._key = address, key
        self._attr_name, self._attr_device_class = SENSORS[key]
        self._attr_unique_id = f"{DOMAIN}_{address}_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, str(address))})

    @property
    def _v(self):
        return self.coordinator.data[self._addr].get(self._key)

    @property
    def is_on(self):
        if self._key == "malfunctionControl":
            return str(self._v).strip() not in ("--", "", "None", "0")  # "--" = nessun errore
        return self._v == 1  # ponytail: status==1 = online, ipotesi da confermare con un'unità scollegata

    @property
    def extra_state_attributes(self):
        return {"codice_errore": self._v} if self._key == "malfunctionControl" else None
