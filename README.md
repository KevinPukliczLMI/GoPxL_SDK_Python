# GoPxL SDK (Python)

Python SDK for programmatic control of **Gocator / GoPxL** sensors — connect, configure, and receive profile, surface, image, and measurement data over REST and GDP.

**Version:** 0.3.0

## Requirements

- Python 3.9+
- [msgpack](https://pypi.org/project/msgpack/) (installed automatically with the SDK)

## Get started

### 1. Install the SDK

```bash
pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
```

Pin a release:

```bash
pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git@v0.3.0
```

Import in your project:

```python
from gopxl_sdk import GoSystem, GoGdpClient, MessageType
```

No source checkout is required — `pip` installs the library into your Python environment.

### 2. Get the sample scripts (optional)

Sample applications are separate from the library. Download **only** the `samples/` folder if you want runnable examples without cloning the full SDK source:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/kevinpuklicz/GoPxL_SDK_Python.git gopxl-samples
cd gopxl-samples
git sparse-checkout set samples
```

On Windows (PowerShell), the same commands work if Git 2.25+ is installed.

### 3. Run a sample

```bash
cd samples
python discover.py
python receive_profile.py --ip 192.168.1.30 --port 3600
python receive_2d_image.py --ip 192.168.1.10
python resource_api/resource_subscriptions.py
```

Each sample accepts `--ip` and `--port`. Samples use the installed `gopxl_sdk` package — you do not need the SDK source on disk.

| Device | Engine id | Try these samples |
|--------|-----------|-------------------|
| Laser line profiler (e.g. 2530) | `LMILaserLineProfiler` | `receive_profile`, `receive_surface`, `receive_measurement` |
| SmartCam / 2D camera (e.g. 1120-M) | `2dscanner` | `receive_2d_image`, `acquire_2d_image` |

Full sample index: [samples/README.md](samples/README.md)

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

UDP discovery binds to port **3320** and broadcasts from each local interface:

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
    "/scan/engines/LMILaserLineProfiler/scanners/scanner-0/sensors/sensor-0"
)
sensor.cache()

with sensor.scoped_update():
    sensor.set_string("displayName", "My Sensor")
    sensor.set_int("/parameters/exposureSettings/singleExposure", 1200)

print(sensor.get_string("displayName"))
system.disconnect()
```

On SmartCam / 1120-M devices use the `2dscanner` engine path instead:

`/scan/engines/2dscanner/scanners/scanner-0/sensors/sensor-0`

See `samples/resource_api/` for subscriptions, schema, and commands.

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

## For SDK developers

Clone the full repository only if you are modifying the SDK itself:

```bash
git clone https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
cd GoPxL_SDK_Python
pip install -e .
```

## License

MIT — Copyright (C) LMI Technologies Inc.
