from __future__ import annotations

from pathlib import Path
import sys


OLD_SHA = "47b917812b96c0f03a18ff7d9d50cddeb8700a72"
NEW_SHA = "4fde185ada8cadb97abf4e831a72204a09b63ecc"
OLD_SHORT = "47b91781"
NEW_SHORT = "4fde185a"
OLD_WORKFLOW = ".github/workflows/wickhunter-wh09-deploy-20260805-v5.yml"
NEW_WORKFLOW = ".github/workflows/wickhunter-wh09-deploy-20260805-v6.yml"


def replace_required(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count == 0:
        raise SystemExit(f"required marker absent: {old!r}")
    return text.replace(old, new)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate.py SOURCE OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    text = source.read_text(encoding="utf-8")
    text = replace_required(text, OLD_WORKFLOW, NEW_WORKFLOW)
    text = replace_required(text, OLD_SHA, NEW_SHA)
    text = replace_required(text, OLD_SHORT, NEW_SHORT)
    text = replace_required(text, "v5", "v6")

    required = (
        "name: WickHunter WH09 fresh PAPER deployment v6",
        "group: wickhunter-wh09-deploy-v6",
        f"EXPECTED_BASE_SHA: {NEW_SHA}",
        f"IMPLEMENTATION_SHA: {NEW_SHA}",
        NEW_WORKFLOW,
        "ACTIVATION_NAME: wickhunter-wh09-activation-20260805-v6-4fde185a",
        "BOT_INSTANCE: wickhunter-paper-v6",
        "OPERATOR_CONTAINER: wickhunter-paper-runtime-v6",
        "GATEWAY_CONTAINER: wickhunter-wh09-egress-v6",
        "INTERNAL_NETWORK: wickhunter-wh09-internal-v6",
        f"OPERATOR_IMAGE: local/wickhunter-paper-runtime:sha-{NEW_SHA}",
        f"GATEWAY_IMAGE: local/wickhunter-paper-egress:sha-{NEW_SHA}",
        'state_runner="$RUNNER_STATE_ROOT/wickhunter-paper-runtime/v6"',
        'state_host="$HOST_STATE_ROOT/wickhunter-paper-runtime/v6"',
        'operator = by_name["wickhunter-paper-runtime-v6"]',
        'gateway = by_name["wickhunter-wh09-egress-v6"]',
        '"operator_container": "wickhunter-paper-runtime-v6"',
        '"gateway_container": "wickhunter-wh09-egress-v6"',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"generated workflow missing markers: {missing!r}")

    forbidden = (OLD_WORKFLOW, OLD_SHA, OLD_SHORT, "v5")
    present = [item for item in forbidden if item in text]
    if present:
        raise SystemExit(f"generated workflow retains stale markers: {present!r}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
