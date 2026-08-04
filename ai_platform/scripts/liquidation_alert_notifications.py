from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from zoneinfo import ZoneInfo


OPERATIONAL_TITLE = "[liquidations-live] operational health alert"
DELIVERY_FAILURE_TITLE = "[liquidations-live] Telegram delivery failure"
STATE_MARKER = "<!-- liquidations-live-telegram-state:v1 -->"
HEALTH_WORKFLOW = "liquidations-live-operational-health.yml"
HEALTH_STATUS_CONTEXT = "liquidations-live-health"
NOTIFICATION_STATUS_CONTEXT = "liquidations-live-notification"
WARSAW = ZoneInfo("Europe/Warsaw")
REMINDER_MS = 60 * 60 * 1000
STALE_MONITOR_MS = 60 * 60 * 1000
QUEUED_LIMIT_MS = 2 * 60 * 1000


class GitHubClient(Protocol):
    def list_issues(self, repository: str, *, state: str = "all") -> list[dict[str, Any]]: ...

    def get_issue(self, repository: str, issue_number: int) -> dict[str, Any]: ...

    def create_issue(self, repository: str, *, title: str, body: str) -> dict[str, Any]: ...

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]: ...

    def list_comments(self, repository: str, issue_number: int) -> list[dict[str, Any]]: ...

    def create_comment(
        self, repository: str, issue_number: int, *, body: str
    ) -> dict[str, Any]: ...

    def update_comment(self, repository: str, comment_id: int, *, body: str) -> dict[str, Any]: ...

    def list_workflow_runs(self, repository: str, workflow: str) -> list[dict[str, Any]]: ...

    def combined_status(self, repository: str, sha: str) -> dict[str, Any]: ...

    def create_status(
        self,
        repository: str,
        sha: str,
        *,
        state: str,
        context: str,
        description: str,
        target_url: str | None,
    ) -> None: ...


class GitHubApiClient:
    def __init__(self, token: str, *, api_url: str = "https://api.github.com") -> None:
        if not token:
            raise ValueError("GitHub token is required")
        self._token = token
        self._api_url = api_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode()
        request = urllib.request.Request(  # noqa: S310
            f"{self._api_url}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "freqtrade-liquidations-telegram-monitor",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
                raw = response.read()
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"GitHub API request failed with HTTP {error.code}") from error
        except urllib.error.URLError as error:
            raise RuntimeError("GitHub API request failed") from error
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))

    def list_issues(self, repository: str, *, state: str = "all") -> list[dict[str, Any]]:
        query = urllib.parse.urlencode(
            {"state": state, "sort": "updated", "direction": "desc", "per_page": 100}
        )
        payload = self._request("GET", f"/repos/{repository}/issues?{query}")
        if not isinstance(payload, list):
            raise RuntimeError("GitHub issues response is not a list")
        return [item for item in payload if isinstance(item, dict) and "pull_request" not in item]

    def get_issue(self, repository: str, issue_number: int) -> dict[str, Any]:
        payload = self._request("GET", f"/repos/{repository}/issues/{issue_number}")
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub issue response is not an object")
        return payload

    def create_issue(self, repository: str, *, title: str, body: str) -> dict[str, Any]:
        payload = self._request(
            "POST", f"/repos/{repository}/issues", {"title": title, "body": body}
        )
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub issue creation response is not an object")
        return payload

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        update: dict[str, Any] = {}
        if body is not None:
            update["body"] = body
        if state is not None:
            update["state"] = state
        payload = self._request("PATCH", f"/repos/{repository}/issues/{issue_number}", update)
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub issue update response is not an object")
        return payload

    def list_comments(self, repository: str, issue_number: int) -> list[dict[str, Any]]:
        payload = self._request(
            "GET", f"/repos/{repository}/issues/{issue_number}/comments?per_page=100"
        )
        if not isinstance(payload, list):
            raise RuntimeError("GitHub comments response is not a list")
        return [item for item in payload if isinstance(item, dict)]

    def create_comment(self, repository: str, issue_number: int, *, body: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/repos/{repository}/issues/{issue_number}/comments",
            {"body": body},
        )
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub comment creation response is not an object")
        return payload

    def update_comment(self, repository: str, comment_id: int, *, body: str) -> dict[str, Any]:
        payload = self._request(
            "PATCH", f"/repos/{repository}/issues/comments/{comment_id}", {"body": body}
        )
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub comment update response is not an object")
        return payload

    def list_workflow_runs(self, repository: str, workflow: str) -> list[dict[str, Any]]:
        query = urllib.parse.urlencode({"branch": "develop", "per_page": 20})
        payload = self._request(
            "GET", f"/repos/{repository}/actions/workflows/{workflow}/runs?{query}"
        )
        runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
        if not isinstance(runs, list):
            raise RuntimeError("GitHub workflow runs response is invalid")
        return [item for item in runs if isinstance(item, dict)]

    def combined_status(self, repository: str, sha: str) -> dict[str, Any]:
        payload = self._request("GET", f"/repos/{repository}/commits/{sha}/status")
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub combined status response is not an object")
        return payload

    def create_status(
        self,
        repository: str,
        sha: str,
        *,
        state: str,
        context: str,
        description: str,
        target_url: str | None,
    ) -> None:
        payload: dict[str, Any] = {
            "state": state,
            "context": context,
            "description": description[:140],
        }
        if target_url:
            payload["target_url"] = target_url
        self._request("POST", f"/repos/{repository}/statuses/{sha}", payload)


@dataclass(frozen=True)
class Incident:
    healthy: bool
    codes: tuple[str, ...]
    description: str
    components: dict[str, str]
    commit_sha: str
    run_url: str
    issue_number: int | None
    issue_closed: bool

    @property
    def fingerprint(self) -> str:
        return "|".join(sorted(self.codes))


@dataclass(frozen=True)
class Decision:
    action: Literal["alert", "update", "reminder", "recovery", "none"]
    state: dict[str, Any]


def _epoch_ms(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


def _format_time(epoch_ms: int) -> str:
    return (
        datetime.fromtimestamp(epoch_ms / 1000, tz=UTC)
        .astimezone(WARSAW)
        .strftime("%Y-%m-%d %H:%M:%S Europe/Warsaw")
    )


def _duration(epoch_ms: int) -> str:
    seconds = max(0, epoch_ms // 1000)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours} h {minutes} min"
    if minutes:
        return f"{minutes} min {seconds} s"
    return f"{seconds} s"


def _extract_json_report(body: str) -> dict[str, Any]:
    for match in re.finditer(r"```json\s*(\{.*?\})\s*```", body, flags=re.DOTALL):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _codes_from_issue(issue: dict[str, Any], report: dict[str, Any]) -> tuple[str, ...]:
    alerts = report.get("alerts")
    codes = {
        str(item.get("code"))
        for item in (alerts if isinstance(alerts, list) else [])
        if isinstance(item, dict) and item.get("code")
    }
    body = str(issue.get("body") or "")
    codes.update(re.findall(r"(?:Code|Kod):\s*`?([A-Z0-9_]+)`?", body))
    return tuple(sorted(codes or {"LIQUIDATIONS_HEALTH_UNKNOWN_FAILURE"}))


def _health_word(value: object, healthy: str, unhealthy: str) -> str:
    return healthy if value is True else unhealthy


def _components(report: dict[str, Any], codes: tuple[str, ...]) -> dict[str, str]:
    raw_checks = report.get("checks")
    checks = raw_checks if isinstance(raw_checks, dict) else {}
    raw_container = checks.get("container")
    raw_state = checks.get("state")
    raw_sources = checks.get("sources")
    raw_disk = checks.get("disk")
    raw_portal = checks.get("portal")
    container = raw_container if isinstance(raw_container, dict) else {}
    state = raw_state if isinstance(raw_state, dict) else {}
    sources = raw_sources if isinstance(raw_sources, dict) else {}
    disk = raw_disk if isinstance(raw_disk, dict) else {}
    portal = raw_portal if isinstance(raw_portal, dict) else {}
    runner_bad = any(
        code
        in {
            "LIQUIDATIONS_HEALTH_RUNNER_UNAVAILABLE",
            "LIQUIDATIONS_HEALTH_RUN_QUEUED",
        }
        for code in codes
    )
    monitor_stale = "LIQUIDATIONS_HEALTH_MONITOR_STALE" in codes
    collector_ok = container.get("healthy") is True and state.get("healthy") is True
    binance = sources.get("binance-usdm")
    bybit = sources.get("bybit-linear")
    binance_health = binance.get("healthy") if isinstance(binance, dict) else None
    bybit_health = bybit.get("healthy") if isinstance(bybit, dict) else None
    return {
        "Portal": _health_word(portal.get("healthy"), "zdrowy", "niedostępny"),
        "Kolektor": _health_word(collector_ok, "zdrowy", "niezdrowy"),
        "Binance": _health_word(
            binance_health,
            "połączony",
            "rozłączony lub niezweryfikowany",
        ),
        "Bybit": _health_word(
            bybit_health,
            "połączony",
            "rozłączony lub niezweryfikowany",
        ),
        "Dysk": _health_word(disk.get("healthy"), "w normie", "poza limitem lub niezweryfikowany"),
        "Runner Synology": (
            "niedostępny" if runner_bad else "niezweryfikowany" if monitor_stale else "online"
        ),
    }


def _first_action(codes: tuple[str, ...]) -> str:
    joined = " ".join(codes)
    if "MONITOR_STALE" in joined:
        return (
            "Sprawdź harmonogram `Liquidations Live Health` i jego najnowszy run; "
            "brak świeżego wyniku nie dowodzi niedostępności runnera."
        )
    if "RUNNER" in joined or "QUEUED" in joined:
        return (
            "Sprawdź kontener runnera `freqtrade-synology-staging-runner` "
            "i jego rejestrację w GitHub Actions."
        )
    if "PORTAL" in joined:
        return (
            "Sprawdź `freqtrade-portal-staging`, jego obraz, politykę restartu "
            "i chroniony endpoint health."
        )
    if "CONTAINER" in joined or "COLLECTOR" in joined or "STATE" in joined:
        return "Sprawdź kontener `liquid20-live` oraz świeżość `/data/live/live-state-v1.json`."
    if "DISK" in joined:
        return "Sprawdź pojemność wolumenu `/volume1/docker/freqtrade-liquidations/data`."
    if "SOURCE" in joined:
        return "Sprawdź połączenia WebSocket Binance USDM, Bybit Linear i OKX Swap."
    return "Otwórz wskazany run GitHub Actions i sprawdź pierwszy czerwony krok."


def decide_notification(
    prior: dict[str, Any] | None, incident: Incident, *, now_ms: int
) -> Decision:
    previous = prior if isinstance(prior, dict) else {}
    was_unhealthy = previous.get("status") == "unhealthy"
    if incident.healthy:
        if not was_unhealthy:
            return Decision("none", {"status": "healthy", "updated_at_ms": now_ms})
        started_at_ms = int(previous.get("started_at_ms") or now_ms)
        return Decision(
            "recovery",
            {
                "status": "healthy",
                "updated_at_ms": now_ms,
                "recovered_at_ms": now_ms,
                "started_at_ms": started_at_ms,
                "last_fingerprint": previous.get("fingerprint"),
                "last_codes": previous.get("codes", []),
            },
        )

    fingerprint = incident.fingerprint
    if not was_unhealthy:
        action: Literal["alert", "update", "reminder", "recovery", "none"] = "alert"
        started_at_ms = now_ms
    else:
        started_at_ms = int(previous.get("started_at_ms") or now_ms)
        if previous.get("fingerprint") != fingerprint:
            action = "update"
        elif now_ms - int(previous.get("last_sent_at_ms") or 0) >= REMINDER_MS:
            action = "reminder"
        else:
            action = "none"
    state = {
        "status": "unhealthy",
        "fingerprint": fingerprint,
        "codes": list(incident.codes),
        "started_at_ms": started_at_ms,
        "updated_at_ms": now_ms,
        "last_sent_at_ms": now_ms if action != "none" else previous.get("last_sent_at_ms"),
    }
    return Decision(action, state)


def _state_body(state: dict[str, Any]) -> str:
    return f"{STATE_MARKER}\n```json\n{json.dumps(state, sort_keys=True)}\n```"


def _load_state(
    client: GitHubClient, repository: str, issue_number: int
) -> tuple[dict[str, Any] | None, int | None]:
    for comment in client.list_comments(repository, issue_number):
        body = str(comment.get("body") or "")
        if STATE_MARKER not in body:
            continue
        payload = _extract_json_report(body)
        return (payload if payload else None, int(comment["id"]))
    return None, None


def _save_state(
    client: GitHubClient,
    repository: str,
    issue_number: int,
    state: dict[str, Any],
    comment_id: int | None,
) -> None:
    body = _state_body(state)
    if comment_id is None:
        client.create_comment(repository, issue_number, body=body)
    else:
        client.update_comment(repository, comment_id, body=body)


def render_failure_message(incident: Incident, decision: Decision, *, now_ms: int) -> str:
    started_at_ms = int(decision.state.get("started_at_ms") or now_ms)
    heading = {
        "alert": "🚨 Liquidations Live — AWARIA",
        "update": "🚨 Liquidations Live — AKTUALIZACJA AWARII",
        "reminder": "🚨 Liquidations Live — AWARIA NADAL TRWA",
    }[decision.action]
    lines = [
        heading,
        "",
        "Środowisko: produkcyjne",
        f"Czas: {_format_time(now_ms)}",
        f"Kod: {', '.join(incident.codes)}",
        f"Opis: {incident.description}",
    ]
    lines.extend(f"{name}: {value}" for name, value in incident.components.items())
    lines.extend(
        [
            f"Od: {_format_time(started_at_ms)}",
            f"Czas trwania: {_duration(now_ms - started_at_ms)}",
            f"Commit: {incident.commit_sha or 'nieznany'}",
            f"GitHub run: {incident.run_url or 'niedostępny'}",
            f"Issue: #{incident.issue_number}" if incident.issue_number else "Issue: niedostępne",
            f"Pierwsza czynność: {_first_action(incident.codes)}",
        ]
    )
    return "\n".join(lines)


def render_recovery_message(incident: Incident, decision: Decision, *, now_ms: int) -> str:
    started_at_ms = int(decision.state.get("started_at_ms") or now_ms)
    restored = ", ".join(str(code) for code in decision.state.get("last_codes", [])) or "system"
    return "\n".join(
        [
            "✅ Liquidations Live — PRZYWRÓCONO",
            "",
            "Środowisko: produkcyjne",
            f"Czas przywrócenia: {_format_time(now_ms)}",
            f"Łączny czas awarii: {_duration(now_ms - started_at_ms)}",
            f"Przywrócony komponent/kod: {restored}",
            f"Run potwierdzający recovery: {incident.run_url or 'niedostępny'}",
            f"Commit: {incident.commit_sha or 'nieznany'}",
            (
                f"Issue: #{incident.issue_number} zostało automatycznie zamknięte."
                if incident.issue_number and incident.issue_closed
                else "Issue: brak potwierdzenia automatycznego zamknięcia."
            ),
        ]
    )


def send_telegram(token: str, chat_id: str, text: str) -> None:
    if not token or not chat_id:
        raise RuntimeError(
            "Missing LIQUIDATIONS_ALERT_TELEGRAM_BOT_TOKEN or LIQUIDATIONS_ALERT_TELEGRAM_CHAT_ID"
        )
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            raw = response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Telegram API request failed with HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError("Telegram API request failed") from error
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("Telegram API returned an invalid response") from error
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError("Telegram API rejected the notification")


def _find_issue(
    issues: list[dict[str, Any]], title: str, *, state: str | None = None
) -> dict[str, Any] | None:
    return next(
        (
            issue
            for issue in issues
            if issue.get("title") == title and (state is None or issue.get("state") == state)
        ),
        None,
    )


def _final_status_present(client: GitHubClient, repository: str, sha: str) -> bool:
    payload = client.combined_status(repository, sha)
    statuses = payload.get("statuses") if isinstance(payload, dict) else None
    return any(
        isinstance(item, dict)
        and item.get("context") == HEALTH_STATUS_CONTEXT
        and item.get("state") in {"success", "failure", "error"}
        for item in statuses or []
    )


def _ensure_watchdog_issue(
    client: GitHubClient,
    repository: str,
    issues: list[dict[str, Any]],
    *,
    code: str,
    description: str,
    run_url: str,
) -> dict[str, Any]:
    existing = _find_issue(issues, OPERATIONAL_TITLE, state="open")
    if existing is not None:
        return existing
    body = "\n".join(
        [
            "<!-- liquidations-live-operational-health -->",
            "## Liquidations Live monitoring failure",
            "",
            f"- Code: `{code}`",
            f"- Workflow run: {run_url or 'unavailable'}",
            "",
            description,
        ]
    )
    return client.create_issue(repository, title=OPERATIONAL_TITLE, body=body)


def discover_incident(
    client: GitHubClient,
    repository: str,
    *,
    now_ms: int,
    issue_number: int | None = None,
) -> tuple[Incident, dict[str, Any]]:
    issues = client.list_issues(repository, state="all")
    issue = client.get_issue(repository, issue_number) if issue_number else None
    if issue is None or issue.get("title") != OPERATIONAL_TITLE:
        issue = _find_issue(issues, OPERATIONAL_TITLE, state="open") or _find_issue(
            issues, OPERATIONAL_TITLE
        )

    open_issue_report = (
        _extract_json_report(str(issue.get("body") or ""))
        if issue is not None and issue.get("state") == "open"
        else {}
    )

    runs = client.list_workflow_runs(repository, HEALTH_WORKFLOW)
    latest = runs[0] if runs else {}
    run_url = str(latest.get("html_url") or "")
    sha = str(latest.get("head_sha") or os.environ.get("GITHUB_SHA", ""))
    created_at_ms = _epoch_ms(str(latest.get("created_at") or ""))
    status = latest.get("status")
    conclusion = latest.get("conclusion")

    synthetic_code = None
    synthetic_description = None
    latest_is_stale = not latest or created_at_ms is None
    if created_at_ms is not None and now_ms - created_at_ms > STALE_MONITOR_MS:
        latest_is_stale = True
    if latest_is_stale and not open_issue_report:
        synthetic_code = "LIQUIDATIONS_HEALTH_MONITOR_STALE"
        synthetic_description = "Brak prawidłowego uruchomienia monitoringu przez ponad 60 minut."
    elif (
        status == "queued"
        and created_at_ms is not None
        and now_ms - created_at_ms > QUEUED_LIMIT_MS
    ):
        synthetic_code = "LIQUIDATIONS_HEALTH_RUN_QUEUED"
        synthetic_description = (
            "Run health pozostaje w kolejce dłużej niż zakontraktowane 120 sekund."
        )
    elif status == "completed" and conclusion == "cancelled":
        synthetic_code = "LIQUIDATIONS_HEALTH_RUN_CANCELLED"
        synthetic_description = (
            "Najnowszy run health został anulowany bez nowszego prawidłowego runu."
        )
    elif (
        status == "completed"
        and conclusion not in {"success", "cancelled"}
        and not (issue and issue.get("state") == "open")
    ):
        synthetic_code = "LIQUIDATIONS_HEALTH_RUN_FAILED_WITHOUT_ALERT"
        synthetic_description = (
            "Run health zakończył się błędem, ale nie pozostawił otwartego alertu."
        )
    elif sha and status == "completed" and not _final_status_present(client, repository, sha):
        synthetic_code = "LIQUIDATIONS_HEALTH_STATUS_MISSING"
        synthetic_description = "Najnowszy run nie opublikował finalnego statusu commita."

    codes: tuple[str, ...]
    report: dict[str, Any]
    if synthetic_code:
        issue = _ensure_watchdog_issue(
            client,
            repository,
            issues,
            code=synthetic_code,
            description=synthetic_description or synthetic_code,
            run_url=run_url,
        )
        codes = (synthetic_code,)
        report = {}
        healthy = False
        description = synthetic_description or synthetic_code
    elif issue is not None and issue.get("state") == "open":
        report = open_issue_report
        codes = _codes_from_issue(issue, report)
        healthy = False
        description = (
            "; ".join(
                str(item.get("message"))
                for item in report.get("alerts", [])
                if isinstance(item, dict) and item.get("message")
            )
            or "Monitoring wykrył awarię Liquidations Live."
        )
    else:
        report = {}
        codes = ()
        event_confirms_recovery = bool(
            issue is not None and issue.get("state") == "closed" and issue_number is not None
        )
        run_is_fresh_and_active = status in {
            "queued",
            "in_progress",
            "pending",
            "requested",
            "waiting",
        }
        healthy = (
            event_confirms_recovery
            or (status == "completed" and conclusion == "success")
            or run_is_fresh_and_active
        )
        description = (
            "Monitoring jest w toku; brak nowej potwierdzonej awarii."
            if run_is_fresh_and_active and not event_confirms_recovery
            else "Wszystkie kontrole Liquidations Live zakończyły się sukcesem."
        )

    number = int(issue["number"]) if isinstance(issue, dict) and issue.get("number") else None
    return (
        Incident(
            healthy=healthy,
            codes=codes,
            description=description[:700],
            components=_components(report, codes),
            commit_sha=str(report.get("checks", {}).get("portal", {}).get("commit_sha") or sha),
            run_url=run_url,
            issue_number=number,
            issue_closed=bool(issue and issue.get("state") == "closed"),
        ),
        issue or {},
    )


def _reconcile_delivery_issue(
    client: GitHubClient,
    repository: str,
    *,
    failed: bool,
    error: str | None,
    run_url: str,
) -> None:
    issues = client.list_issues(repository, state="all")
    issue = _find_issue(issues, DELIVERY_FAILURE_TITLE, state="open")
    if failed:
        body = "\n".join(
            [
                "<!-- liquidations-live-telegram-delivery-failure -->",
                "## Telegram delivery failure",
                "",
                f"- Workflow run: {run_url or 'unavailable'}",
                f"- Safe error: `{(error or 'unknown failure')[:300]}`",
                "",
                "The original Liquidations Live failure remains authoritative and is not masked.",
            ]
        )
        if issue is None:
            client.create_issue(repository, title=DELIVERY_FAILURE_TITLE, body=body)
        else:
            client.update_issue(repository, int(issue["number"]), body=body)
    elif issue is not None:
        client.update_issue(repository, int(issue["number"]), state="closed")


def _bootstrap_messages(now_ms: int, run_url: str, sha: str) -> list[str]:
    timestamp = _format_time(now_ms)
    return [
        "\n".join(
            [
                "🧪 TEST — Liquidations Live",
                "Kanał Telegram działa.",
                f"Czas: {timestamp}",
                f"Commit: {sha or 'nieznany'}",
                f"GitHub run: {run_url}",
                "Ten test nie zmienia stanu produkcyjnego, Issue, kolektora, portalu ani tradingu.",
            ]
        ),
        "\n".join(
            [
                "🧪 TEST — 🚨 Liquidations Live — AWARIA KONTROLOWANA",
                "Kod: CONTROLLED_NOTIFICATION_TEST",
                f"Czas: {timestamp}",
                f"GitHub run: {run_url}",
                "To wyłącznie test dostarczenia; produkcja nie została wyłączona.",
            ]
        ),
        "\n".join(
            [
                "🧪 TEST — ✅ Liquidations Live — PRZYWRÓCONO",
                f"Czas przywrócenia: {timestamp}",
                f"GitHub run: {run_url}",
                "To wyłącznie test recovery; stan produkcyjny i Issue nie zostały zmienione.",
            ]
        ),
    ]


def run(
    *,
    client: GitHubClient,
    repository: str,
    token: str,
    chat_id: str,
    mode: str,
    issue_number: int | None,
    now_ms: int,
    sender: Callable[[str, str, str], None] = send_telegram,
) -> int:
    run_url = (
        os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        + "/"
        + repository
        + "/actions/runs/"
        + os.environ.get("GITHUB_RUN_ID", "unknown")
    )
    sha = os.environ.get("GITHUB_SHA", "")
    if mode in {"bootstrap", "test", "controlled_failure", "controlled_recovery"}:
        messages = _bootstrap_messages(now_ms, run_url, sha)
        selected = {
            "test": messages[:1],
            "controlled_failure": messages[1:2],
            "controlled_recovery": messages[2:3],
            "bootstrap": messages,
        }[mode]
        try:
            for message in selected:
                sender(token, chat_id, message)
        except RuntimeError as error:
            _reconcile_delivery_issue(
                client, repository, failed=True, error=str(error), run_url=run_url
            )
            if sha:
                client.create_status(
                    repository,
                    sha,
                    state="failure",
                    context=NOTIFICATION_STATUS_CONTEXT,
                    description="Telegram delivery failed",
                    target_url=run_url,
                )
            return 1
        _reconcile_delivery_issue(client, repository, failed=False, error=None, run_url=run_url)
        if sha:
            client.create_status(
                repository,
                sha,
                state="success",
                context=NOTIFICATION_STATUS_CONTEXT,
                description="Telegram notification channel verified",
                target_url=run_url,
            )
        return 0

    incident, _issue = discover_incident(
        client, repository, now_ms=now_ms, issue_number=issue_number
    )
    if incident.issue_number is None:
        return 0 if incident.healthy else 1
    prior, comment_id = _load_state(client, repository, incident.issue_number)
    decision = decide_notification(prior, incident, now_ms=now_ms)
    if decision.action == "none":
        _save_state(client, repository, incident.issue_number, decision.state, comment_id)
        return 0
    if decision.action == "recovery":
        message = render_recovery_message(incident, decision, now_ms=now_ms)
    else:
        message = render_failure_message(incident, decision, now_ms=now_ms)
    try:
        sender(token, chat_id, message)
    except RuntimeError as error:
        _reconcile_delivery_issue(
            client, repository, failed=True, error=str(error), run_url=run_url
        )
        target_sha = incident.commit_sha or sha
        if target_sha:
            client.create_status(
                repository,
                target_sha,
                state="failure",
                context=NOTIFICATION_STATUS_CONTEXT,
                description="Telegram delivery failed",
                target_url=run_url,
            )
        return 1
    _save_state(client, repository, incident.issue_number, decision.state, comment_id)
    _reconcile_delivery_issue(client, repository, failed=False, error=None, run_url=run_url)
    target_sha = incident.commit_sha or sha
    if target_sha:
        client.create_status(
            repository,
            target_sha,
            state="success",
            context=NOTIFICATION_STATUS_CONTEXT,
            description="Telegram notification delivered",
            target_url=run_url,
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deliver deduplicated Liquidations Live Telegram alerts."
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "bootstrap", "test", "controlled_failure", "controlled_recovery"),
        default="auto",
    )
    parser.add_argument("--issue-number", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    github_token = os.environ.get("GH_TOKEN", "")
    if not repository or not github_token:
        print("GitHub repository and token are required", file=sys.stderr)
        return 2
    client = GitHubApiClient(
        github_token, api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com")
    )
    return run(
        client=client,
        repository=repository,
        token=os.environ.get("LIQUIDATIONS_ALERT_TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.environ.get("LIQUIDATIONS_ALERT_TELEGRAM_CHAT_ID", ""),
        mode=args.mode,
        issue_number=args.issue_number,
        now_ms=time.time_ns() // 1_000_000,
    )


if __name__ == "__main__":
    sys.exit(main())
