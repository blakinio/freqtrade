# Compose static review

## v1 and v2 collector controls confirmed

- non-root configurable UID/GID;
- `read_only: true`;
- `cap_drop: ALL`;
- `no-new-privileges:true`;
- PID and memory limits;
- request bind read-only;
- durable state bind read-write;
- hardened `/tmp` tmpfs;
- no published ports;
- no host networking;
- dedicated bridge egress.

## Defect

Both daemons classify `CAPTURE_REQUEST_UNAVAILABLE` as `blocked` but write `healthy=true`. Both healthchecks and request deployment probes accept that state. See `WH-ME-AUD-004`.

## Dynamic validation

`docker compose config --quiet` and rendered-Compose checks were not run because the primary audit environment had no repository checkout/Docker capability.
