from __future__ import annotations

from pathlib import Path


_CONFIG_PATH = (
    Path(__file__).resolve().parents[4]
    / "ai_platform/portal/deploy/observability/otel-collector.example.yaml"
)


def test_collector_redacts_sensitive_attributes_before_every_exporter() -> None:
    config = _CONFIG_PATH.read_text(encoding="utf-8")

    assert "redaction/sensitive:" in config
    assert "allow_all_keys: true" in config
    assert "summary: silent" in config
    for sensitive_pattern in (
        "api[_-]?key",
        "authorization",
        "cookie",
        "passphrase",
        "password",
        "private[_-]?key",
        "secret",
        "token",
    ):
        assert sensitive_pattern in config

    protected_pipeline = (
        "processors: [memory_limiter, resource/environment, redaction/sensitive, batch]"
    )
    assert config.count(protected_pipeline) == 3


def test_collector_destinations_and_authorization_remain_environment_provided() -> None:
    config = _CONFIG_PATH.read_text(encoding="utf-8")

    assert "http://" not in config
    assert "https://" not in config
    for variable in (
        "PORTAL_OTEL_LOGS_ENDPOINT",
        "PORTAL_OTEL_LOGS_AUTHORIZATION",
        "PORTAL_OTEL_TRACES_ENDPOINT",
        "PORTAL_OTEL_TRACES_AUTHORIZATION",
        "PORTAL_OTEL_METRICS_ENDPOINT",
        "PORTAL_OTEL_METRICS_AUTHORIZATION",
    ):
        assert f"${{env:{variable}}}" in config
