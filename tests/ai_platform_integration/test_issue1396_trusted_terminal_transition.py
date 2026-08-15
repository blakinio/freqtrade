from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "synology"
    / "wickhunter-paper-runtime"
    / "issue1396_trusted_terminal_transition.py"
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "issue1396_trusted_transition_tested",
        MODULE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_material_binds_current_gateway_and_authorization_identity() -> None:
    module = _load_module()
    old = SimpleNamespace(
        strategy_artifact_digest="1" * 64,
        model_artifact_digest="2" * 64,
        feature_schema_version="features-v1",
        exchange_mode="dry-run-public-market-data",
        exchange_connection_revision="exchange-revision-v1",
    )
    args = SimpleNamespace(
        config_digest="3" * 64,
        image_digest="4" * 64,
        internal_network="wickhunter-production-paper-internal",
        gateway_artifact_digest="5" * 64,
        gateway_contract_digest="6" * 64,
        market_egress_policy_digest="7" * 64,
        authorization_id="issue1396-paper-auth-v4",
        authorization_digest="8" * 64,
        candidate_package_id="candidate-package-v1",
        candidate_manifest="9" * 64,
    )

    material = module._paper_material(old, args)

    assert material.runtime_image_digest == "4" * 64
    assert material.normalized_runtime_config_digest == "3" * 64
    assert material.gateway_artifact_digest == "5" * 64
    assert material.gateway_contract_digest == "6" * 64
    assert material.market_data_egress_policy_digest == "7" * 64
    assert material.paper_activation_authorized is True
    assert material.paper_authorization_id == "issue1396-paper-auth-v4"
    assert material.paper_authorization_digest == "8" * 64
    assert material.paper_candidate_package_id == "candidate-package-v1"
    assert material.paper_candidate_manifest_sha256 == "9" * 64
    assert material.generation_spec_version == "wh09-paper-production-generation-v3"


def test_source_time_uses_checked_at_ms() -> None:
    module = _load_module()
    expected = datetime(2026, 8, 15, 8, 0, tzinfo=UTC)
    checked_at_ms = int(expected.timestamp() * 1000)

    assert module._source_time({"checked_at_ms": checked_at_ms}) == expected


def test_author_paper_parser_requires_gateway_identity_digests() -> None:
    module = _load_module()
    parser = module.parser()
    args = parser.parse_args(
        [
            "author-paper",
            "--implementation-sha",
            "a" * 40,
            "--image-digest",
            "1" * 64,
            "--config-digest",
            "2" * 64,
            "--authorization-id",
            "authorization-v1",
            "--authorization-digest",
            "3" * 64,
            "--candidate-package-id",
            "candidate-v1",
            "--candidate-manifest",
            "4" * 64,
            "--internal-network",
            "paper-internal",
            "--gateway-artifact-digest",
            "5" * 64,
            "--gateway-contract-digest",
            "6" * 64,
            "--market-egress-policy-digest",
            "7" * 64,
        ]
    )

    assert args.gateway_artifact_digest == "5" * 64
    assert args.gateway_contract_digest == "6" * 64
    assert args.market_egress_policy_digest == "7" * 64
