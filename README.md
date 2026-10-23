# Bosch VRF ACC for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Custom integration that talks to the web UI of a **Bosch VRF centralized controller (ACC)**
and exposes every indoor unit (IDU) in Home Assistant. Local polling, no cloud.

> Unofficial project, not affiliated with Bosch. It uses the same JSON-RPC calls as the
> controller's web interface, so it may break after a firmware update. Commands are sent to
> your real air conditioning system: test on a single unit first.

## Tested on

| | |
|---|---|
| Controller | Bosch ACC, hardware `acc 2.1`, software `4.0.0.36` |
| Indoor units | `IDU_V4_MINI_VRF` over RS-485 (XYE protocol v4), 15 units |

Other ACC versions or unit models may work but have not been tested. Reports are welcome via issues.

## Entities

Each IDU becomes one device with:

| Entity | Details |
|---|---|
| `climate` | on/off, mode (fan only, cool, heat), target temperature (0.5 °C steps, limits read from the unit), fan speed (`auto`, 1–7), room temperature |
| `sensor` | Setpoint, Room temperature |
| `binary_sensor` | Alarm (problem, with the error code as attribute), Connection |

The device name is the room name configured on the ACC (e.g. `IDU-00-00`).

## Installation

### HACS (custom repository)
1. HACS → ⋮ → **Custom repositories** → add `https://github.com/davidemassaro/ha-bosch-vrf-acc`, type **Integration**.
2. Install **Bosch VRF ACC** and restart Home Assistant.

### Manual
Copy `custom_components/bosch_vrf` into your Home Assistant `config/custom_components/` folder and restart.

## Configuration

Settings → Devices & services → **Add integration** → *Bosch VRF ACC*, then enter:

- **Host**: IP address of the ACC
- **Username** / **Password**: the same credentials you use for the ACC web interface

To change the IP or the credentials later: integration menu (⋮) → **Reconfigure**.

## How it works
- Values are refreshed every **30 seconds** (one `getAllIdus` request for all units) and right after every command.
- The session is kept between requests; if it expires the integration logs in again automatically.
- The ACC uses a self-signed certificate, so TLS verification is disabled.

## Known limitations
- **Dry mode** is disabled: it exists on the ACC (`modeControl` = 6) but is not supported by the tested VRF. To re-enable it, uncomment the line in `MODES` in `climate.py`.
- Setpoint and fan speed may be locked by the unit in some modes.
- "Connection" assumes `status == 1` means online (not verified with an unplugged unit).

## Debugging helper

`acc_status.py` is a standalone CLI that prints the raw IDU data (requires `pip install requests`):

```bash
python acc_status.py --host 192.168.1.10                 # table with all units
python acc_status.py --host 192.168.1.10 -a 0 --json     # full JSON of the unit with address 0
```

Credentials are read from `ACC_USER` / `ACC_PASS` or asked interactively.

## License

[MIT](LICENSE)
