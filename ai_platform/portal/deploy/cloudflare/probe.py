from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urljoin

import httpx

from ai_platform.portal.deploy.cloudflare.policy import load_policy, policy_violations
from ai_platform.portal.deploy.cloudflare.schema import StagingIngressPolicy


class ProbeOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ProbeResult:
    name: str
    outcome: ProbeOutcome
    evidence: str


def _required_env(policy: StagingIngressPolicy, name: str) -> str:
    env_name = getattr(policy, name)
    value = os.environ.get(env_name, "").strip()
    if not value:
        raise RuntimeError(f"required staging environment reference is unset: {env_name}")
    return value


def _required_url(policy: StagingIngressPolicy, name: str) -> str:
    env_name = getattr(policy, name)
    value = _required_env(policy, name)
    try:
        url = httpx.URL(value)
    except ValueError as exc:
        raise RuntimeError(f"invalid URL in staging environment reference: {env_name}") from exc
    if url.scheme not in {"http", "https"} or not url.host:
        raise RuntimeError(f"invalid URL in staging environment reference: {env_name}")
    if url.userinfo:
        raise RuntimeError(f"credentials are forbidden in staging URL reference: {env_name}")
    return str(url)


def _required_path(policy: StagingIngressPolicy, name: str) -> str:
    env_name = getattr(policy, name)
    value = _required_env(policy, name)
    if not value.startswith("/") or "://" in value:
        raise RuntimeError(f"invalid relative path in staging environment reference: {env_name}")
    return value


def _is_access_redirect(response: httpx.Response) -> bool:
    location = response.headers.get("location", "").casefold()
    return response.is_redirect and (
        "cloudflareaccess.com" in location or "/cdn-cgi/access/" in location
    )


def _request_result(
    client: httpx.Client,
    name: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[httpx.Response | None, ProbeResult | None]:
    try:
        return client.get(url, headers=headers), None
    except httpx.RequestError as exc:
        return None, ProbeResult(name, ProbeOutcome.FAIL, f"unreachable:{type(exc).__name__}")


def _deny_probe(client: httpx.Client, name: str, url: str) -> ProbeResult:
    try:
        response = client.get(url)
    except httpx.RequestError as exc:
        return ProbeResult(name, ProbeOutcome.PASS, f"unreachable:{type(exc).__name__}")
    if response.status_code in {401, 403, 421, 451}:
        return ProbeResult(name, ProbeOutcome.PASS, f"denied:http-{response.status_code}")
    return ProbeResult(
        name,
        ProbeOutcome.FAIL,
        f"unexpected-public-response:http-{response.status_code}",
    )


def run_probes(
    policy: StagingIngressPolicy,
    transport: httpx.BaseTransport | None = None,
) -> tuple[ProbeResult, ...]:
    violations = policy_violations(policy)
    if violations:
        raise RuntimeError("invalid staging policy: " + "; ".join(violations))

    base_url = _required_url(policy, "public_base_url_env")
    privileged_path = _required_path(policy, "privileged_path_env")
    origin_url = _required_url(policy, "origin_probe_url_env")
    freqtrade_url = _required_url(policy, "freqtrade_probe_url_env")
    client_id = _required_env(policy, "access_client_id_env")
    client_secret = _required_env(policy, "access_client_secret_env")
    privileged_url = urljoin(base_url.rstrip("/") + "/", privileged_path.lstrip("/"))

    results: list[ProbeResult] = []
    with httpx.Client(follow_redirects=False, timeout=10.0, transport=transport) as client:
        public, public_error = _request_result(client, "cloudflare-public-ingress", base_url)
        if public_error is not None:
            results.append(public_error)
        else:
            assert public is not None
            public_ok = 200 <= public.status_code < 400
            results.append(
                ProbeResult(
                    "cloudflare-public-ingress",
                    ProbeOutcome.PASS if public_ok else ProbeOutcome.FAIL,
                    f"http-{public.status_code}",
                )
            )

        anonymous, anonymous_error = _request_result(
            client,
            "access-anonymous-denial",
            privileged_url,
        )
        if anonymous_error is not None:
            results.append(anonymous_error)
        else:
            assert anonymous is not None
            anonymous_denied = anonymous.status_code in {401, 403} or _is_access_redirect(anonymous)
            results.append(
                ProbeResult(
                    "access-anonymous-denial",
                    ProbeOutcome.PASS if anonymous_denied else ProbeOutcome.FAIL,
                    f"http-{anonymous.status_code}",
                )
            )

        service, service_error = _request_result(
            client,
            "access-service-identity",
            privileged_url,
            headers={
                "CF-Access-Client-Id": client_id,
                "CF-Access-Client-Secret": client_secret,
            },
        )
        if service_error is not None:
            results.append(service_error)
        else:
            assert service is not None
            service_allowed = 200 <= service.status_code < 400 and not _is_access_redirect(service)
            results.append(
                ProbeResult(
                    "access-service-identity",
                    ProbeOutcome.PASS if service_allowed else ProbeOutcome.FAIL,
                    f"http-{service.status_code}",
                )
            )

        results.append(_deny_probe(client, "origin-direct-denial", origin_url))
        results.append(_deny_probe(client, "freqtrade-direct-denial", freqtrade_url))
    return tuple(results)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe real Cloudflare-protected staging boundaries"
    )
    parser.add_argument("--policy", required=True, type=Path)
    args = parser.parse_args()
    try:
        results = run_probes(load_policy(args.policy))
    except (OSError, RuntimeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, indent=2))
        return 2
    payload = {
        "passed": all(result.outcome is ProbeOutcome.PASS for result in results),
        "results": [asdict(result) for result in results],
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
