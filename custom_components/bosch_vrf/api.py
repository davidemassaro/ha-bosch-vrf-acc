"""Client sincrono per la web UI JSON-RPC dell'ACC Bosch (da usare in executor)."""
import base64

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


class ACC:
    def __init__(self, host: str, user: str, password: str, timeout: int = 10):
        self.base = f"https://{host}"
        self.user, self.password, self.timeout = user, password, timeout
        self.s = requests.Session()
        self.s.verify = False  # certificato self-signed sull'IP
        self.s.headers.update({"Origin": self.base, "Referer": self.base + "/"})

    def login(self) -> None:
        r = self.s.post(
            self.base + "/system/http/login",
            data={"u": _b64(self.user), "p": _b64(self.password), "referer": "/system/http"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        who = self.rpc("UserManager/getCurrentUser")
        if not isinstance(who, dict) or not who.get("LoginName"):
            raise RuntimeError("login failed")

    def rpc(self, method: str, params=None):
        r = self.s.post(
            self.base + "/remote/json-rpc/posts",
            json={"jsonrpc": "2.0", "method": method, "params": params or [], "id": 123},
            timeout=self.timeout,
        )
        r.raise_for_status()
        j = r.json()
        if "error" in j:
            raise RuntimeError(f"{method}: {j['error']}")
        return j.get("result")

    def _call(self, method: str, params=None):
        try:
            return self.rpc(method, params)
        except (requests.RequestException, RuntimeError):
            self.login()  # sessione scaduta: rilogga e riprova una volta
            return self.rpc(method, params)

    def get_idus(self) -> list[dict]:
        return self._call("IDUManager/getAllIdus")

    def set_property(self, uri: str, prop: str, value) -> None:
        self._call("IDUManager/setPropertyForIdus", [[uri], prop, value])
