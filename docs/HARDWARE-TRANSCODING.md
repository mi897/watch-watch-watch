# Hardware transcoding (optional, off by default)

Direct play needs no GPU. Enable this only if clients force transcoding and your CPU struggles. Setup is host-specific, so we document the approach rather than ship untested override files.

## Intel / AMD (VAAPI, QSV) on Linux
Add to the `jellyfin` service in a local `compose.override.yaml`:
```
services:
  jellyfin:
    devices:
      - /dev/dri:/dev/dri
    group_add:
      - "<render group id>"   # run: getent group render | cut -d: -f3
```
Then enable VAAPI or QSV in Jellyfin: Dashboard, Playback, Transcoding.

## NVIDIA
Install the NVIDIA Container Toolkit on the host, then give the service GPU access with a Compose `deploy.resources.reservations.devices` entry (driver `nvidia`, capabilities `gpu`) and choose NVENC in the same dashboard page.

Check Jellyfin's hardware acceleration docs for your GPU generation. We have not tested these on real hardware.
