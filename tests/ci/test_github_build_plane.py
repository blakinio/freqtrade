import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PORTAL_WORKFLOW = ROOT / ".github/workflows/portal-oidc-public-deploy.yml"
PORTAL_WICKHUNTER_ADOPTION_WORKFLOW = ROOT / ".github/workflows/portal-wickhunter-wh09-adoption.yml"
WICKHUNTER_WORKFLOW = (
    ROOT / ".github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml"
)
LIQUID20_WORKFLOW = ROOT / ".github/workflows/liquidations-live-synology.yml"
PACKAGE_CLEANUP_WORKFLOW = ROOT / ".github/workflows/packages-cleanup.yml"
LIQUID20_DEPLOY = ROOT / "deploy/synology/liquid20/deploy-live.sh"
DOWNLOAD_ARTIFACT_SHA = "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
DELETE_PACKAGE_SHA = "e5bc658cc4c965c472efe991f8beea3981499c55"


def _split_jobs(workflow: str, first_job: str, second_job: str) -> tuple[str, str]:
    first_marker = f"  {first_job}:\n"
    second_marker = f"  {second_job}:\n"
    assert first_marker in workflow
    assert second_marker in workflow
    first_start = workflow.index(first_marker)
    second_start = workflow.index(second_marker, first_start + len(first_marker))
    return workflow[first_start:second_start], workflow[second_start:]


def test_portal_build_scan_is_hosted_and_transitional_synology_only_materializes_images() -> None:
    workflow = PORTAL_WORKFLOW.read_text(encoding="utf-8")
    build, deploy = _split_jobs(workflow, "build-approved-images", "deploy")

    assert "runs-on: ubuntu-24.04" in build
    assert "packages: write" in build
    assert "portal_supply_chain.py build-verify" in build
    assert "Install checksum-pinned Syft and Grype" in build
    assert 'docker push "$control_tag"' in build
    assert 'docker push "$web_tag"' in build
    assert "control_ref=" in build
    assert "web_ref=" in build
    assert "retention-days: 1" in build

    assert "needs: build-approved-images" in deploy
    assert "runs-on: [freqtrade-staging]" in deploy
    assert "packages: read" in deploy
    assert "portal_supply_chain.py build-verify" not in deploy
    assert "Install checksum-pinned Syft and Grype" not in deploy
    assert f"actions/download-artifact@{DOWNLOAD_ARTIFACT_SHA}" in deploy
    assert 'docker pull "$CONTROL_REF"' in deploy
    assert 'docker pull "$WEB_REF"' in deploy
    assert "portal_supply_chain.py verify-approval" in deploy
    assert "portal_supply_chain.py deploy-approved" in deploy
    assert "rebuilt_during_deploy" in deploy


def test_portal_deployment_trigger_remains_bounded_to_frozen_request() -> None:
    workflow = PORTAL_WORKFLOW.read_text(encoding="utf-8")
    pre_jobs = workflow.split("jobs:\n", maxsplit=1)[0]
    request = "deploy/synology/portal-oidc/run-requests/public-oidc-20260801-v1.json"
    assert request in pre_jobs
    assert "workflow_dispatch:" not in pre_jobs
    assert "push:" not in pre_jobs


def test_wickhunter_image_build_is_hosted_and_transitional_synology_keeps_target_checks() -> None:
    workflow = WICKHUNTER_WORKFLOW.read_text(encoding="utf-8")
    build, deploy = _split_jobs(workflow, "build-runtime-image", "deploy")

    assert "runs-on: ubuntu-24.04" in build
    assert "packages: write" in build
    assert "docker build --no-cache --progress=plain" in build
    assert "ghcr.io/blakinio/wickhunter-production-research-runtime" in build
    assert "org.opencontainers.image.revision" in build
    assert "image_ref=" in build
    assert "image_id=" in build

    assert "needs: build-runtime-image" in deploy
    assert "freqtrade-staging" in deploy
    assert "packages: read" in deploy
    assert "docker build --no-cache" not in deploy
    assert 'docker pull "$BUILT_IMAGE_REF"' in deploy
    assert '[[ "$image_id" == "$BUILT_IMAGE_ID" ]]' in deploy
    assert "--no-build --force-recreate --remove-orphans" in deploy
    assert "HOST_PID_UID_ISOLATION_PASS" in deploy
    assert "LIQUID20_ACTIVE_RUN_ID" in deploy
    assert "live_capital_authorized" in deploy
    assert "orders_submitted" in deploy
    assert "automatic_promotion_enabled" in deploy


def test_wickhunter_trigger_stays_one_shot_and_synology_is_only_transitional_deploy() -> None:
    workflow = WICKHUNTER_WORKFLOW.read_text(encoding="utf-8")
    pre_jobs = workflow.split("jobs:\n", maxsplit=1)[0]
    request = (
        "deploy/synology/wickhunter-production-research-runtime/run-requests/"
        "retry-wh09-production-research-20260819-v7.json"
    )
    assert request in pre_jobs
    assert "schedule:" not in pre_jobs
    assert "workflow_dispatch:" not in pre_jobs
    _, deploy = _split_jobs(workflow, "build-runtime-image", "deploy")
    assert "freqtrade-staging" in deploy
    assert "runs-on: ubuntu-24.04" not in deploy


def test_wickhunter_portal_adoption_builds_portal_on_hosted_and_synology_only_deploys() -> None:
    workflow = PORTAL_WICKHUNTER_ADOPTION_WORKFLOW.read_text(encoding="utf-8")
    build, adopt = _split_jobs(workflow, "build-portal-images", "adopt")
    assert "runs-on: ubuntu-24.04" in build
    assert "packages: write" in build
    assert "portal_supply_chain.py build-verify" in build
    assert 'docker push "$control_tag"' in build
    assert 'docker push "$web_tag"' in build
    assert "retention-days: 1" in build
    assert "needs: build-portal-images" in adopt
    assert "freqtrade-staging" in adopt
    assert "packages: read" in adopt
    assert "portal_supply_chain.py build-verify" not in adopt
    assert "actions/download-artifact@" in adopt
    assert 'docker pull "$CONTROL_REF"' in adopt
    assert 'docker pull "$WEB_REF"' in adopt
    assert "Wait for exact WH09 redeploy to converge" in adopt
    assert "Prove WH09 restart persistence and idempotent adoption" in adopt
    assert 'docker restart "$before_id"' in adopt
    assert '"duplicate_registration": False' in adopt
    assert '"restart_persistence": True' in adopt
    terminal = adopt.split("Enforce terminal zero-authority evidence", 1)[1]
    assert 'report.get("decision_count", 0) <= 0' in terminal
    assert 'report.get("no_trade_count", 0) <= 0' in terminal
    assert 'report.get("latest_decision") is None' in terminal
    assert 'report.get("post_restart_decision_count", 0) <= 0' in terminal
    assert 'report.get("post_restart_no_trade_count", 0) <= 0' in terminal
    assert 'report.get("post_restart_latest_decision") is None' in terminal


def test_liquid20_image_build_is_hosted_and_transitional_synology_deploys_exact_image() -> None:
    workflow = LIQUID20_WORKFLOW.read_text(encoding="utf-8")
    build, deploy = _split_jobs(workflow, "build-image", "deploy")

    assert "runs-on: ubuntu-24.04" in build
    assert "packages: write" in build
    assert "docker build" in build
    assert "ghcr.io/blakinio/liquid20-collector" in build
    assert "org.opencontainers.image.revision" in build
    assert "image_ref=" in build
    assert "image_id=" in build

    assert "needs: build-image" in deploy
    assert "runs-on: freqtrade-staging" in deploy
    assert "packages: read" in deploy
    assert "docker build" not in deploy
    assert 'docker pull "$BUILT_IMAGE_REF"' in deploy
    assert "LIQUID20_PREBUILT_IMAGE: ${{ needs.build-image.outputs.image_ref }}" in deploy
    assert "RUNNER_ARCH_VALUE" in deploy
    assert "refusing incompatible Synology runner architecture" in deploy


def test_liquid20_actions_path_refuses_transitional_synology_build_fallback() -> None:
    script = LIQUID20_DEPLOY.read_text(encoding="utf-8")
    prebuilt = 'if [[ -n "$prebuilt_image" ]]'
    actions_guard = 'elif [[ "${GITHUB_ACTIONS:-}" == "true" ]]'
    refusal = "refusing Synology build fallback"
    build = "docker build"

    assert prebuilt in script
    assert actions_guard in script
    assert refusal in script
    assert "ghcr\\.io/blakinio/liquid20-collector@sha256" in script
    assert script.index(prebuilt) < script.index(actions_guard)
    assert script.index(actions_guard) < script.index(refusal)
    assert script.index(refusal) < script.index(build)


def test_liquid20_deployment_script_has_valid_bash_syntax() -> None:
    subprocess.run(["bash", "-n", str(LIQUID20_DEPLOY)], check=True)


def test_liquid20_preserves_candidate_rollback_and_public_data_runtime_checks() -> None:
    script = LIQUID20_DEPLOY.read_text(encoding="utf-8")

    assert "Restoring previous live collector image" in script
    assert "candidate_first=" in script
    assert "candidate_second=" in script
    assert "history_before=" in script
    assert "history_after=" in script
    assert 'test "$history_before" = "$history_after"' in script
    assert '"trading_authorized": False' in script
    for source in ("bybit-linear", "binance-usdm", "okx-swap"):
        assert source in script


def test_fork_build_plane_packages_have_exact_bounded_retention_policy() -> None:
    workflow = PACKAGE_CLEANUP_WORKFLOW.read_text(encoding="utf-8")
    _, fork_cleanup = _split_jobs(workflow, "deploy-docker", "cleanup-fork-build-plane")

    assert "github.repository == 'blakinio/freqtrade'" in fork_cleanup
    assert "runs-on: ubuntu-24.04" in fork_cleanup
    assert "packages: write" in fork_cleanup
    assert f"actions/delete-package-versions@{DELETE_PACKAGE_SHA}" in fork_cleanup
    assert "min-versions-to-keep: 10" in fork_cleanup
    assert "delete-only-untagged-versions" not in fork_cleanup
    for package in (
        "freqtrade-portal-control-plane",
        "freqtrade-portal-web",
        "wickhunter-production-research-runtime",
        "liquid20-collector",
    ):
        assert f"inputs.package_name == '{package}'" in fork_cleanup
