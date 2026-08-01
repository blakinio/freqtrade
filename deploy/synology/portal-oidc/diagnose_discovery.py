#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from typing import Any


CONTROL_CONTAINER = "freqtrade-portal-control-plane"
AUTHENTIK_ORIGIN = "https://auth.molehill.cloud"
ISSUER = f"{AUTHENTIK_ORIGIN}/application/o/freqtrade-portal/"
PUBLIC_PORTAL_LOGIN_PREFIX = "https://quant.molehill.cloud/api/identity/login"
OIDC_HTTP_USER_AGENT = "Freqtrade-Portal-OIDC/1.0"
MAX_DETAIL = 1000


def _probe_script() -> str:
    return f"""
import json
import urllib.error
import urllib.request
issuer = {ISSUER!r}
headers = {{
    'Accept': 'application/json',
    'User-Agent': {OIDC_HTTP_USER_AGENT!r},
}}
def load_json(url, phase):
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')), response.status
    except urllib.error.HTTPError as exc:
        raise SystemExit(f'{{phase}} HTTP {{exc.code}}') from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f'{{phase}} URL error: {{exc.reason}}') from exc
discovery_url = issuer.rstrip('/') + '/.well-known/openid-configuration'
discovery, discovery_status = load_json(discovery_url, 'discovery')
if discovery.get('issuer') != issuer:
    raise SystemExit('issuer mismatch')
for key in ('authorization_endpoint', 'token_endpoint', 'jwks_uri'):
    value = discovery.get(key)
    if not isinstance(value, str) or not value.startswith({AUTHENTIK_ORIGIN!r} + '/'):
        raise SystemExit('invalid endpoint: ' + key)
jwks, jwks_status = load_json(discovery['jwks_uri'], 'jwks')
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


def _install_public_portal_probe_user_agent() -> None:
    if getattr(urllib.request.Request, "_portal_oidc_machine_user_agent", False):
        return

    class PortalPublicProbeRequest(urllib.request.Request):
        _portal_oidc_machine_user_agent = True

        def __init__(
            self,
            url: str,
            data: bytes | None = None,
            headers: dict[str, str] | None = None,
            origin_req_host: str | None = None,
            unverifiable: bool = False,
            method: str | None = None,
        ) -> None:
            prepared_headers = dict(headers or {})
            if url.startswith(PUBLIC_PORTAL_LOGIN_PREFIX) and not any(
                name.lower() == "user-agent" for name in prepared_headers
            ):
                prepared_headers["User-Agent"] = OIDC_HTTP_USER_AGENT
            super().__init__(
                url,
                data=data,
                headers=prepared_headers,
                origin_req_host=origin_req_host,
                unverifiable=unverifiable,
                method=method,
            )

    urllib.request.Request = PortalPublicProbeRequest  # type: ignore[misc]


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


def deployment_probe(error_type: type[Exception]) -> tuple[dict[str, Any], dict[str, int]]:
    try:
        payload = diagnose()
    except RuntimeError as exc:
        raise error_type(str(exc)) from exc
    discovery_status = payload.get("discovery")
    jwks_status = payload.get("jwks_uri")
    if type(discovery_status) is not int or type(jwks_status) is not int:
        raise error_type("discovery diagnostic returned invalid HTTP status values")
    _install_public_portal_probe_user_agent()
    return {"issuer": ISSUER}, {
        "discovery": discovery_status,
        "jwks_uri": jwks_status,
    }


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
