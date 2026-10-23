import voluptuous as vol
from homeassistant import config_entries

from .api import ACC

DOMAIN = "bosch_vrf"


def _schema(d=None):
    d = d or {}
    return vol.Schema({
        vol.Required("host", default=d.get("host", "")): str,
        vol.Required("username", default=d.get("username", "")): str,
        vol.Required("password", default=d.get("password", "")): str,
    })


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _try_login(self, data) -> bool:
        try:
            await self.hass.async_add_executor_job(ACC(data["host"], data["username"], data["password"]).login)
        except Exception:
            return False
        return True

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            await self.async_set_unique_id(user_input["host"])
            self._abort_if_unique_id_configured()
            if await self._try_login(user_input):
                return self.async_create_entry(title=f"ACC {user_input['host']}", data=user_input)
            errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="user", data_schema=_schema(user_input), errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        """Modifica host/credenziali di un'integrazione già configurata."""
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input:
            if await self._try_login(user_input):
                return self.async_update_reload_and_abort(
                    entry, unique_id=user_input["host"],
                    title=f"ACC {user_input['host']}", data=user_input,
                )
            errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="reconfigure", data_schema=_schema(user_input or entry.data), errors=errors
        )
