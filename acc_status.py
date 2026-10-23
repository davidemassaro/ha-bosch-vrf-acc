#!/usr/bin/env python3
"""Log in to the Bosch ACC (web UI) and read the status of all IDUs.

Credentials (optional; if missing they are asked interactively):
    Linux/macOS:  export ACC_USER='user'; export ACC_PASS='password'
    Windows cmd:  set ACC_USER=user  and  set ACC_PASS=password

Usage (--host is required):
    python3 acc_status.py --host 192.168.1.10                  # table with all units
    python3 acc_status.py --host 192.168.1.10 --json           # full JSON
    python3 acc_status.py --host 192.168.1.10 -a 0 5 --json    # only the units with address 0 and 5

Requires: pip install requests
"""
import argparse
import base64
import getpass
import json
import os
import sys

import requests
import urllib3

RPC_PATH = "/remote/json-rpc/posts"
LOGIN_PATH = "/system/http/login"

def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


class ACC:
    def __init__(self, host: str, verify: bool = False, timeout: int = 10):
        self.base = f"https://{host}"
        self.timeout = timeout
        self.s = requests.Session()
        self.s.verify = verify  # self-signed certificate on the IP
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.s.headers.update({"Origin": self.base, "Referer": self.base + "/"})

    def login(self, user: str, password: str) -> None:
        r = self.s.post(
            self.base + LOGIN_PATH,
            data={"u": b64(user), "p": b64(password), "referer": "/system/http"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        # Does login return 200 even with wrong credentials? Unknown:
        # the real check is an authenticated RPC.
        who = self.rpc("UserManager/getCurrentUser")
        if not isinstance(who, dict) or not who.get("LoginName"):
            raise RuntimeError(f"Login failed, getCurrentUser = {who!r}")
        if not self.s.cookies:
            print("WARNING: no session cookie received: "
                  "authentication may be handled differently.", file=sys.stderr)

    def rpc(self, method: str, params=None):
        body = {"jsonrpc": "2.0", "method": method, "params": params or [], "id": 123}
        r = self.s.post(self.base + RPC_PATH, json=body, timeout=self.timeout)
        r.raise_for_status()
        j = r.json()
        if "error" in j:
            raise RuntimeError(f"{method}: {j['error']}")
        return j.get("result")


def fmt(v):
    return "-" if v is None else str(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", required=True, help="ACC IP or hostname")
    ap.add_argument("--address", "-a", type=int, nargs="+", help="show only these IDUs (e.g. -a 0 5 17)")
    ap.add_argument("--json", action="store_true", help="print the full getAllIdus JSON")
    ap.add_argument("--verify-tls", action="store_true", help="verify the TLS certificate (default: no)")
    args = ap.parse_args()

    user = os.environ.get("ACC_USER") or input("User: ")
    password = os.environ.get("ACC_PASS") or getpass.getpass("Password: ")

    acc = ACC(args.host, verify=args.verify_tls)
    acc.login(user, password)

    idus = acc.rpc("IDUManager/getAllIdus")
    if args.address:
        idus = [x for x in idus if x.get("address") in args.address]
    if args.json:
        print(json.dumps(idus, indent=2, ensure_ascii=False))
        return

    idus.sort(key=lambda x: x.get("address", 0))
    cols = [
        ("addr", "address"), ("name", "roomName"), ("on", "iduPowerOnControl"),
        ("mode", "modeControl"), ("fan", "fanSpeedDcControl"),
        ("setpoint", "temperatureSettingControl"), ("room", "roomTemperature"),
        ("T2A", "T2A"), ("T2B", "T2B"), ("error", "malfunctionControl"),
    ]
    rows = [[fmt(x.get(k)) for _, k in cols] for x in idus]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, (h, _) in enumerate(cols)]
    print("  ".join(h.ljust(w) for (h, _), w in zip(cols, widths)))
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))
    print(f"\n{len(idus)} units")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
