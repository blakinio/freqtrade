from __future__ import annotations

import subprocess
from pathlib import Path


SOURCE_BRANCH = "ops/wickhunter-wh09-deploy-paper-20260805-v9"
SOURCE_PATH = ".github/workflows/wickhunter-wh09-deploy-20260805-v9.yml"
TARGET_PATH = Path(".github/workflows/wickhunter-wh09-deploy-20260805-v10.yml")
OLD_IMPLEMENTATION_SHA = "7e191cebc71118a2dee32dceeec49a47153dd8f8"
NEW_IMPLEMENTATION_SHA = "e9c04506f8dce9df26ae63006229e0d48f1f4209"
OLD_SHORT_SHA = "7e191ceb"
NEW_SHORT_SHA = "e9c04506"


def main() -> None:
    source = subprocess.check_output(
        ["git", "show", f"origin/{SOURCE_BRANCH}:{SOURCE_PATH}"],
        text=True,
    )
    if source.count(OLD_IMPLEMENTATION_SHA) < 3:
        raise SystemExit("v9 workflow does not contain expected implementation bindings")
    if source.count("v9") < 10:
        raise SystemExit("v9 workflow does not contain expected fresh identities")

    generated = source.replace(OLD_IMPLEMENTATION_SHA, NEW_IMPLEMENTATION_SHA)
    generated = generated.replace(OLD_SHORT_SHA, NEW_SHORT_SHA)
    generated = generated.replace("v9", "v10").replace("V9", "V10")

    forbidden = (OLD_IMPLEMENTATION_SHA, OLD_SHORT_SHA, "v9", "V9")
    remaining = [value for value in forbidden if value in generated]
    if remaining:
        raise SystemExit(f"generated workflow retains v9 identities: {remaining}")
    required = (
        "name: WickHunter WH09 fresh PAPER deployment v10",
        'WORKFLOW_PATH: .github/workflows/wickhunter-wh09-deploy-20260805-v10.yml',
        f"EXPECTED_BASE_SHA: {NEW_IMPLEMENTATION_SHA}",
        f"IMPLEMENTATION_SHA: {NEW_IMPLEMENTATION_SHA}",
        "ACTIVATION_NAME: wickhunter-wh09-activation-20260805-v10-e9c04506",
        "BOT_INSTANCE: wickhunter-paper-v10",
        "OPERATOR_CONTAINER: wickhunter-paper-runtime-v10",
        "GATEWAY_CONTAINER: wickhunter-wh09-egress-v10",
        "INTERNAL_NETWORK: wickhunter-wh09-internal-v10",
        "state_runner=\"$RUNNER_STATE_ROOT/wickhunter-paper-runtime/v10\"",
        "status\": \"deployed_waiting_prospective_acceptance\"",
        "orders_submitted\": 0",
    )
    missing = [value for value in required if value not in generated]
    if missing:
        raise SystemExit(f"generated workflow is missing required v10 bindings: {missing}")

    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_PATH.exists():
        raise SystemExit("fresh v10 workflow path already exists")
    TARGET_PATH.write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
