# GoPxL Python SDK Samples

Python ports of the GoPxL C++ SDK sample applications. Run any sample with:

```bash
python samples/<sample>.py --ip 192.168.1.10 --port 3600
```

Shared helpers live in `samples/common/`.

| Sample | Description |
| --- | --- |
| `discover.py` | Discover GoPxL instances and visible sensors on the network |
| `configure_sensor.py` | Configure triggers, exposure, active area, and digital I/O |
| `configure_tool.py` | Add and configure a Profile Bounding Box tool |
| `receive_profile.py` | Receive uniform profile data via GDP |
| `receive_surface.py` | Receive surface data via GDP |
| `receive_image.py` | Receive heightmap image data via GDP |
| `receive_measurement.py` | Receive tool measurement output via GDP |
| `receive_string.py` | Receive tool string output via GDP |
| `receive_metrics.py` | Stream REST metrics with callbacks |
| `receive_async.py` | Receive GDP data asynchronously |
| `receive_2d_image.py` | Receive 2D camera images via GDP |
| `acquire_2d_image.py` | Software-trigger 2D image acquisition |
| `save_job.py` | Save, rename, download, and load jobs |
| `replay_data.py` | Record live data and replay via GDP |
| `backup_restore.py` | Archive and restore sensor configuration |
| `align_sensor.py` | Run alignment and read calibration transform |
| `system_upgrade.py` | Upload firmware package (`upgrade_archive.dat`) |
| `multi_sensor_layout.py` | Multi-sensor scanner layout setup |
| `multilayer_outputs.py` | Multilayer profile array GDP output |
| `resource_api/resource_subscriptions.py` | Subscriptions, caching, child URIs |
| `resource_api/resource_schema.py` | Schema introspection and validation |
| `resource_api/resource_commands.py` | `command_names`, `action_names`, `call_action` |
| `resource_api/resource_configure_sensor.py` | Sensor configuration via GoResource |
| `resource_api/resource_configure_tool.py` | Tool creation/configuration via GoResource |
