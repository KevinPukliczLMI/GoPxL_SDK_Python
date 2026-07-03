# GoPxL SDK (Python)

Python SDK for programmatic control of **Gocator / GoPxL** sensors. Mirrors the official C++ GoPxL SDK (`GoSystem`, `GoRestClient`, `GoGdpClient`, discovery, GDP message parsers, and the v1.5 `GoResource` API).

**Version:** 0.3.0

## Requirements

- Python 3.9+
- [msgpack](https://pypi.org/project/msgpack/) (installed automatically)

## Install

```bash
pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
```

Editable local install:

```bash
git clone https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
cd GoPxL_SDK_Python
pip install -e .
```

Pin a release tag:

```bash
pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git@v0.3.0
```

After install, import as `gopxl_sdk`:

```python
import gopxl_sdk
from gopxl_sdk import GoSystem, GoGdpClient, MessageType
```

## Quick start

Connect, start the device, and receive one GDP dataset:

```python
from gopxl_sdk import GoSystem, GoGdpClient, MessageType
from gopxl_sdk.enums import GoSystemState

ADDRESS = "192.168.1.10"
CONTROL_PORT = 3600
TIMEOUT_MS = 20000

system = GoSystem(ADDRESS, CONTROL_PORT)
system.connect()

started = False
if system.running_state() != GoSystemState.RUNNING:
    system.start()
    started = True

gdp = GoGdpClient()
gdp.connect(system.address(), system.gdp_port())
gdp.receive_data_sync(TIMEOUT_MS)

for msg in gdp.dataset():
    if msg.type() == MessageType.MEASUREMENT:
        print(msg.data_source_id(), msg.value)

gdp.close()
if started:
    system.stop()
system.disconnect()
```

Enable Gocator Protocol outputs before receiving GDP data (see `samples/receive_profile.py`).

## Discovery

```python
from gopxl_sdk import GoDiscoveryClient, GoSystem

discovery = GoDiscoveryClient()
discovery.blocking_discover(timeout_ms=3000)
for inst in discovery.instance_list():
    print(inst.ip_address, inst.app_name, inst.control_port)

    system = GoSystem.from_instance(inst)
    system.connect()
    # ...
    system.disconnect()
```

## GoResource API (v1.5)

Typed, cached access to REST resources with schema validation and subscriptions:

```python
from gopxl_sdk import GoSystem

system = GoSystem("192.168.1.10", 3600)
system.connect()

sensor = system.resource(
    "/scan/engines/LMILaserLineProfiler/scanners/scanner-0/sensors/sensor-0"
)
sensor.cache()

with sensor.scoped_update():
    sensor.set_string("displayName", "My Sensor")
    sensor.set_int("/parameters/exposureSettings/singleExposure", 1200)

print(sensor.get_string("displayName"))
system.disconnect()
```

See `samples/resource_api/` for subscriptions, schema, and commands.

## Samples

24 sample applications under `samples/` — Python ports of the C++ SDK samples. Each accepts `--ip` and `--port`:

```bash
cd samples
python discover.py
python receive_profile.py --ip 192.168.1.10 --port 3600
python resource_api/resource_subscriptions.py
```

Samples bootstrap the SDK from the parent folder via `samples/common/sample_utils.py`, so `pip install` is optional for local development.

Full index: [samples/README.md](samples/README.md)

## API overview

| Component | Description |
|-----------|-------------|
| `GoSystem` | Connect, start/stop, GDP port, sensor paths, resource manager |
| `GoRestClient` | REST CRUD, commands, sub/unsub, streams, notification listeners |
| `GoGdpClient` | GDP TCP streaming (sync and callback-based async receive) |
| `GoDataSet` / GDP messages | Profile, surface, image, stamp, measurement, mesh, spots, rendering, features, signal/null/health |
| `GoDiscoveryClient` | GoPxL UDP discovery (port 3320) and classic Gocator discovery (port 3220) |
| `GoResource` / `GoResourceManager` | Cached resources, schema validation, subscriptions, HAL children, deferred updates |
| `GoSchemaValidator` | Client-side JSON Schema validation |
| Exceptions | `GoRequestError`, `GoChannelError`, `GoResourceError`, `GoResourceValidationError` |

## Project layout

```
GoPxL_SDK_Py/
  __init__.py          # package entry (import as gopxl_sdk)
  system.py            # GoSystem
  rest_client.py       # GoRestClient
  gdp_client.py        # GoGdpClient
  gdp_msg.py           # GDP message parsers
  resource.py          # GoResource
  resource_manager.py  # GoResourceManager
  discovery.py         # GoDiscoveryClient
  pyproject.toml       # pip package metadata (name: gopxl-sdk)
  samples/             # sample applications
```

## C++ SDK parity

This SDK covers the main control-plane workflows: REST, discovery, GDP receive (including images), async GDP with a receive/queue/callback thread model, and the GoResource API.

A few C++ utility types are simplified in Python:

- `GoJson` / `GoUri` wrappers (Python uses `dict` and `json_pointer` helpers)
- Common-header transform / bounding-box fields are skipped during GDP parse

## License

MIT — Copyright (C) LMI Technologies Inc.
