# GoPxL SDK (Python)

Python SDK for **Gocator / GoPxL** sensors. It mirrors the official C++ GoPxL SDK (`GoSystem`, `GoRestClient`, `GoGdpClient`, discovery, GDP parsers, and the v1.5 `GoResource` API) so you can script sensor control without C++.

It is not a full API clone — some C++ types and utilities are simplified or omitted (see [C++ SDK parity](#c-sdk-parity) below). For common tasks such as connecting, configuring sensors, receiving GDP data, and using the Resource API, it should be a practical alternative for Python workflows.

## Install

```bash
pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
```

## Get samples

### Clone from GitHub

Shallow clone the default branch (no branch checkout needed):

```bash
git clone --depth 1 https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
```

Copy samples into your project:

```bash
# Linux / macOS
cp -r GoPxL_SDK_Python/GoPxL_SDK_Py/samples ./samples

# Windows (cmd)
xcopy /E /I GoPxL_SDK_Python\GoPxL_SDK_Py\samples samples
```

Or let the SDK do the clone for you:

```bash
python -m gopxl --from-github
```

### From pip install

From your project folder (not inside the SDK source tree):

```bash
python -m gopxl
```

This copies bundled samples into `./samples`.

Alternatives:

```bash
gopxl-copy-samples
python -m gopxl_sdk --from-github
python -m gopxl_sdk.copy_samples --from-github
```

Optional output path (positional, not `--destination`):

```bash
python -m gopxl ./my_samples
python -m gopxl --from-github ./my_samples
```

## Run

```bash
cd samples
python discover.py
python receive_profile.py --ip 192.168.1.10 --port 3600
```

Each sample defines `SYSTEM_IP`, `CONTROL_PORT`, and `ENGINE_ID` at the top of the file. Override on the command line with `--ip` and `--port`.

---

## Requirements

- Python 3.9+
- [msgpack](https://pypi.org/project/msgpack/) (installed automatically)

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

Enable Gocator Protocol and add GDP outputs before receiving data (see `samples/receive_profile.py` or `samples/receive_2d_image.py`).

## Discovery

UDP discovery binds to port **3320** and broadcasts from each local interface (same model as the C++ SDK):

```python
from gopxl_sdk import GoDiscoveryClient, GoSystem

discovery = GoDiscoveryClient()
discovery.blocking_discover(timeout_ms=3000, classic_discover=True)
for inst in discovery.instance_list():
    print(inst.ip_address, inst.app_name, inst.control_port)

    system = GoSystem.from_instance(inst)
    system.connect()
    # ...
    system.disconnect()
```

The PC and sensor must share a subnet (broadcast does not cross routers).

## GoResource API (v1.5)

Typed, cached access to REST resources with schema validation and subscriptions:

```python
from gopxl_sdk import GoSystem

system = GoSystem("192.168.1.10", 3600)
system.connect()

sensor = system.resource(
    "/scan/engines/2dscanner/scanners/scanner-0/sensors/sensor-0"
)
sensor.cache()

with sensor.scoped_update():
    sensor.set_string("displayName", "My Sensor")
    sensor.set_int("/parameters/exposureSettings/singleExposure", 1200)

print(sensor.get_string("displayName"))
system.disconnect()
```

On other device types, swap the engine id in the path:

| Device | Sensor path |
|--------|-------------|
| Laser line profiler (e.g. 2530) | `/scan/engines/LMILaserLineProfiler/scanners/scanner-0/sensors/sensor-0` |
| Gocator Snapshot (e.g. G3) | `/scan/engines/LMIFringeSnapshot/scanners/scanner-0/sensors/sensor-0` |

See `samples/resource_api/` for subscriptions, schema, and commands.

## Samples

Each sample defines `SYSTEM_IP`, `CONTROL_PORT`, and `ENGINE_ID` at the top of the file. Set `ENGINE_ID` to match your device (`2dscanner` for 1120-M, `LMILaserLineProfiler` for 2530, `LMIFringeSnapshot` for G3 snapshot). Override IP/port on the command line with `--ip` and `--port`.

```bash
cd samples
python discover.py
python receive_profile.py --ip 192.168.1.10 --port 3600
```

**Device types**

| Device | Engine id | Typical samples |
|--------|-----------|-----------------|
| SmartCam / 2D camera (e.g. 1120-M) | `2dscanner` | `receive_2d_image`, `acquire_2d_image` |
| Laser line profiler (e.g. 2530) | `LMILaserLineProfiler` | `receive_profile`, `receive_surface`, `receive_measurement` |
| Gocator Snapshot (e.g. G3) | `LMIFringeSnapshot` | `receive_surface`, `receive_measurement` |

`receive_image.py` and `receive_metrics.py` auto-detect the live engine when possible.

## API overview

| Component | Description |
|-----------|-------------|
| `GoSystem` | Connect, start/stop, GDP port, sensor paths, resource manager |
| `GoRestClient` | REST CRUD, commands, sub/unsub, streams, notification listeners |
| `GoGdpClient` | GDP TCP streaming (sync and async with receive queue + callback thread) |
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

This SDK covers the main control-plane workflows: REST, discovery, GDP receive (profiles, surfaces, images, measurements), async GDP with a receive/queue/callback thread model, and the GoResource API.

GDP common-header transform (3×4 `f32`) and bounding box (6×`f32`) are parsed for wire alignment. Public `GoGdpTransform` / `GoGdpBoundingBox` types and `GoJson` / `GoUri` wrappers are not exposed; Python uses `dict` and `json_pointer` helpers instead.

## Pin a release

```bash
pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git@v0.3.0
```

## For SDK developers

From a local copy of `GoPxL_SDK_Py/`:

```bash
pip install -e .
```

## License

MIT — Copyright (C) LMI Technologies Inc.
