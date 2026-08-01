#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys


CONTROL_CONTAINER = "freqtrade-portal-control-plane"
AUTHENTIK_ORIGIN = "https://auth.molehill.cloud"
ISSUER = f"{AUTHENTIK_ORIGIN}/application/o/freqtrade-portal/"
MAX_DETAIL = 1000


def _probe_script() -> str:
    return f"""
import json
import urllib.request
issuer = {ISSUER!r}
discovery_url = issuer.rstrip('/') + '/.well-known/openid-configuration'
with urllib.request.urlopen(discovery_url, timeout=15) as response:
    discovery = json.loads(response.read().decode('utf-8'))
    discovery_status = response.status
if discovery.get('issuer') != issuer:
    raise SystemExit('issuer mismatch')
for key in ('authorization_endpoint', 'token_endpoint', 'jwks_uri'):
    value = discovery.get(key)
    if not isinstance(value, str) or not value.startswith({AUTHENTIK_ORIGIN!r} + '/'):
        raise SystemExit('invalid endpoint: ' + key)
with urllib.request.urlopen(discovery['jwks_uri'], timeout=15) as response:
    jwks = json.loads(response.read().decode('utf-8'))
    jwks_status = response.status
if not isinstance(jwks.get('keys'), list) or not jwks['keys']:
    raise SystemExit('empty JWKS')
print('__PORTAL_DISCOVERY_DIAGNOSTIC__' + json.dumps({{
    'discovery': discovery_status,
    'jwks_uri': jwks_status,
    'issuer': discovery['issuer'],
}}, sort_keys=True))
""".strip()


def _bounded_detail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [
        line.strip()
        for stream in (result.stdout, result.stderr)
        for line in stream.splitlines()
        if line.strip()
    ]
    if not lines:
        return "no output"
    detail = " | ".join(lines[-8:])
    if len(detail) > MAX_DETAIL:
        return f"{detail[: MAX_DETAIL - 3]}..."
    return detail


def diagnose() -> dict[str, object]:
    result = subprocess.run(
        ["docker", "exec", CONTROL_CONTAINER, "python", "-c", _probe_script()],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"discovery diagnostic failed ({result.returncode}): {_bounded_detail(result)}"
        )
    marker = next(
        (
            line.removeprefix("__PORTAL_DISCOVERY_DIAGNOSTIC__")
            for line in result.stdout.splitlines()
            if line.startswith("__PORTAL_DISCOVERY_DIAGNOSTIC__")
        ),
        None,
    )
    if marker is None:
        raise RuntimeError("discovery diagnostic returned no marker")
    payload = json.loads(marker)
    if payload.get("issuer") != ISSUER:
        raise RuntimeError("discovery diagnostic observed an unexpected issuer")
    return payload


def main() -> int:
    try:
        payload = diagnose()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"status": "success", **payload}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
