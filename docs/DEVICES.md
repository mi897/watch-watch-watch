# Devices

Anything that has a Jellyfin client can connect; enter `http://<server-address>:8096` and sign in. See [REMOTE-ACCESS.md](REMOTE-ACCESS.md) for the address.

| Device | Client |
|--------|--------|
| Any browser | The web UI at the server address |
| Android, Android TV, Fire TV | Official Jellyfin app |
| iPhone, iPad, Apple TV | Official Jellyfin app, Swiftfin, or Infuse (third party) |
| Roku | Official Jellyfin channel |
| LG / Samsung TVs | Jellyfin apps exist for some models (availability varies by year) |
| Kodi | Jellyfin add-on |

Client availability changes; check the Jellyfin client list at jellyfin.org before buying hardware. Direct play avoids transcoding: modern clients play H.264/H.265 MP4/MKV directly, while older TVs may force transcoding (see [HARDWARE-TRANSCODING.md](HARDWARE-TRANSCODING.md)).
