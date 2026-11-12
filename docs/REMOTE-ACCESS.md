# Remote and LAN access

By default Jellyfin is reachable only from the machine itself (`127.0.0.1`). Nothing is exposed to the internet and we ship no tunnel or reverse proxy.

## Other devices on your home network
Edit the `ports:` line of `jellyfin` in `compose.yaml`, replacing `127.0.0.1:` with your server's LAN IP (for example `192.168.1.20:${JELLYFIN_PORT:-8096}:8096`). Binding to a specific LAN address is safer than `0.0.0.0`. Restart with `docker compose up -d`. Do not forward this port on your router.

## Away from home (recommended: a private network)
Use Tailscale or WireGuard so the server is never public.
- **Tailscale:** install on the server and on each device, sign in to the same tailnet, then browse to the server's tailnet name or IP on port 8096 (bind to that address or the LAN address as above).
- **WireGuard:** run your own WireGuard server on your router or host, connect devices to it, then use the server's LAN address.

## Discouraged
Port-forwarding or putting Jellyfin on the public internet. If you do it anyway, you need HTTPS, strong unique passwords and a plan for updates. This project does not support that setup.

## Discovery
Automatic LAN discovery (UDP 7359) and DLNA need host networking. They are off by default; add devices by typing the server address.
