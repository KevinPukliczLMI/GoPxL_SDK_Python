# GoPxL SDK (Python)

Python SDK for Gocator sensors — REST control, GDP data streaming, discovery, and the GoResource API.

## 1. Install the SDK

```bash
pip install git+https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
```

Requires Python 3.9+. The `msgpack` dependency is installed automatically.

## 2. Clone the samples folder

```bash
git clone https://github.com/kevinpuklicz/GoPxL_SDK_Python.git
```

This gives you the full `samples/` tree from the repo — same files, same layout, including `common/`.

## 3. Run a sample

```bash
python discover.py
#or
python receive_profile.py
```

Each script has `SYSTEM_IP`, `CONTROL_PORT`, and `ENGINE_ID` at the top. Override the IP on the command line:

```bash
python receive_profile.py --ip 192.168.1.10 --port 3600
```

---

## Samples

| File | What it does |
|------|----------------|
| `discover.py` | Find sensors on the network |
| `align_sensor.py` | Run sensor alignment |
| `configure_sensor.py` | Set triggers, exposure, and digital I/O |
| `configure_tool.py` | Add and configure a measurement tool |
| `backup_restore.py` | Backup or restore sensor configuration |
| `save_job.py` | Save the active job to the sensor |
| `acquire_2d_image.py` | Software-trigger and receive a 2D image (SmartCam) |
| `receive_2d_image.py` | Receive a 2D image via GDP |
| `receive_image.py` | Receive heightmap image data via GDP |
| `receive_profile.py` | Receive uniform profile data via GDP |
| `receive_surface.py` | Receive surface data via GDP |
| `receive_measurement.py` | Receive tool measurement output via GDP |
| `receive_string.py` | Receive string tool output via GDP |
| `receive_async.py` | Receive GDP data on an async callback |
| `receive_metrics.py` | Stream system/scanner/sensor metrics |
| `replay_data.py` | Receive replayed profile data |
| `multi_sensor_layout.py` | Build a multi-sensor layout |
| `multilayer_outputs.py` | Confocal multilayer GDP outputs |
| `system_upgrade.py` | Upload a firmware package |
| `resource_api/resource_configure_sensor.py` | Configure a sensor via GoResource |
| `resource_api/resource_configure_tool.py` | Configure a tool via GoResource |
| `resource_api/resource_commands.py` | Run REST commands via GoResource |
| `resource_api/resource_schema.py` | Read and validate resource schema |
| `resource_api/resource_subscriptions.py` | Subscribe to resource updates |

| Device | `ENGINE_ID` | Good starting samples |
|--------|-------------|----------------------|
| SmartCam / 2D (e.g. 1120-M) | `2dscanner` | `acquire_2d_image`, `receive_2d_image` |
| Laser profiler (e.g. 2530) | `LMILaserLineProfiler` | `receive_profile`, `receive_surface` |
| Gocator Confocal (G4 / G5) | `LMIConfocalLineProfiler` | `multilayer_outputs`, `receive_profile`, `receive_surface` |
| Snapshot (e.g. G3) | `LMIFringeSnapshot` | `receive_surface`, `receive_measurement` |

---

## Example code

Connect, receive GDP measurements, and disconnect:

```python
from gopxl_sdk import GoSystem, GoGdpClient, MessageType
from gopxl_sdk.enums import GoSystemState

system = GoSystem("192.168.1.10", 3600)
system.connect()

if system.running_state() != GoSystemState.RUNNING:
    system.start()

gdp = GoGdpClient()
gdp.connect(system.address(), system.gdp_port())
gdp.receive_data_sync(20000)

for msg in gdp.dataset():
    if msg.type() == MessageType.MEASUREMENT:
        print(msg.data_source_id(), msg.value)

gdp.close()
system.stop()
system.disconnect()
```

Discover sensors on the network:

```python
from gopxl_sdk import GoDiscoveryClient

discovery = GoDiscoveryClient()
discovery.blocking_discover(timeout_ms=3000, classic_discover=True)
for inst in discovery.instance_list():
    print(inst.ip_address, inst.app_name)
```

---

## SDK files

After `pip install`, these are the main `gopxl_sdk` Python modules:

| File | What it does |
|------|----------------|
| `__init__.py` | Public package exports (`GoSystem`, `GoGdpClient`, etc.) |
| `system.py` | `GoSystem` — connect, start/stop, GDP port, resource access |
| `rest_client.py` | `GoRestClient` — REST read/write, commands, sub/unsub, streams |
| `request.py` | `GoRequest` — builds REST requests sent to the sensor |
| `response.py` | `GoResponse`, `GoRequestResponse`, `GoNotificationResponse`, `GoStreamResponse` |
| `transaction.py` | `GoTransaction` — async request/response pairing with timeouts |
| `gdp_client.py` | `GoGdpClient` — GDP TCP connection, sync and async receive |
| `gdp_msg.py` | GDP message types — profile, surface, image, measurement, stamp, etc. |
| `dataset.py` | `GoDataSet` — collection of messages from one GDP frame |
| `kserializer.py` | Low-level GDP packet read/write (MessagePack over TCP) |
| `discovery.py` | `GoDiscoveryClient` — find GoPxL and Gocator sensors on the network |
| `classic_discovery.py` | Legacy UDP discovery used by older Gocator sensors |
| `instance.py` | `GoInstance` — one discovered sensor (IP, port, model, serial) |
| `resource.py` | `GoResource` — cached REST resource with get/set/update |
| `resource_manager.py` | `GoResourceManager` — creates and tracks `GoResource` objects |
| `schema_validator.py` | Validates resource updates against sensor JSON schema |
| `json_pointer.py` | JSON pointer helpers used by the resource API |
| `enums.py` | `GoStatus`, `GoSystemState`, `MessageType`, `GoRequestMethod`, etc. |
| `exceptions.py` | `GoRequestError`, `GoChannelError`, `GoResourceError`, etc. |
| `def_.py` | Default ports and shared constants |

**Main classes you import:**

```python
from gopxl_sdk import (
    GoSystem,           # system.py
    GoRestClient,       # rest_client.py
    GoGdpClient,        # gdp_client.py
    GoDiscoveryClient,  # discovery.py
    GoResource,         # resource.py
    GoDataSet,          # dataset.py
    MessageType,        # enums.py
)
```

```
gopxl_sdk/
  system.py              GoSystem
  rest_client.py         REST client
  gdp_client.py          GDP client
  gdp_msg.py             GDP parsers
  dataset.py             GDP datasets
  discovery.py           Network discovery
  resource.py            GoResource API
  resource_manager.py    Resource cache/manager
  enums.py               Status codes and message types
  exceptions.py          SDK errors
  samples/               Bundled sample scripts
```

---

## License

MIT — Copyright (C) LMI Technologies Inc.
