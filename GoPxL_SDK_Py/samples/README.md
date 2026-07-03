# GoPxL Python SDK Samples

Python ports of the GoPxL C++ SDK sample applications. Run any sample with:

```bash
python samples/<sample>.py --ip 192.168.1.10 --port 3600
```

Shared helpers live in `samples/common/` (`sample_utils.py`, `gdp_helpers.py`).

## Device types

| Device | Engine id | Use these samples |
|--------|-----------|-------------------|
| Laser line profiler (e.g. 2530) | `LMILaserLineProfiler` | `receive_profile`, `receive_surface`, `configure_sensor`, `configure_tool`, … |
| SmartCam / 2D camera (e.g. 1120-M) | `2dscanner` | `receive_2d_image`, `acquire_2d_image` |

`receive_image.py` and `receive_metrics.py` auto-detect the live engine when possible.

## Sample index

| Sample | Description |
| --- | --- |
| `discover.py` | Discover GoPxL instances and visible sensors (UDP 3320 + classic 3220) |
| `configure_sensor.py` | Configure triggers, exposure, active area, and digital I/O |
| `configure_tool.py` | Add and configure a Profile Bounding Box tool |
| `receive_profile.py` | Receive uniform profile data via GDP |
| `receive_surface.py` | Receive surface data via GDP |
| `receive_image.py` | Receive image data (profiler heightmap or SmartCam 2D, auto-detected) |
| `receive_measurement.py` | Receive tool measurement output via GDP |
| `receive_string.py` | Receive tool string output via GDP |
| `receive_metrics.py` | Stream REST metrics (uptime, CPU, temps, latency) |
| `receive_async.py` | Receive GDP data asynchronously (queued callback thread) |
| `receive_2d_image.py` | Receive 2D camera images via GDP (`2dscanner`) |
| `acquire_2d_image.py` | Acquire 2D image with ImageFilter tool (`2dscanner`) |
| `save_job.py` | Save, rename, download, and load jobs |
| `replay_data.py` | Enable replay and receive GDP data |
| `backup_restore.py` | Archive and restore sensor configuration |
| `align_sensor.py` | Run alignment and read calibration transform |
| `system_upgrade.py` | Inspect firmware upgrade status / packages |
| `multi_sensor_layout.py` | Multi-sensor scanner layout setup |
| `multilayer_outputs.py` | Multilayer profile array GDP output |
| `resource_api/resource_subscriptions.py` | Subscriptions, caching, child URIs |
| `resource_api/resource_schema.py` | Schema introspection and validation |
| `resource_api/resource_commands.py` | `command_names`, `action_names`, `call_action` |
| `resource_api/resource_configure_sensor.py` | Sensor configuration via GoResource |
| `resource_api/resource_configure_tool.py` | Tool creation/configuration via GoResource |
