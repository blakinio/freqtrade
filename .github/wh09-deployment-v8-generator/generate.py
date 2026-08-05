from __future__ import annotations

from pathlib import Path
import sys


OLD_SHA = "4fde185ada8cadb97abf4e831a72204a09b63ecc"
NEW_SHA = "c1d1f9f3db5e95e245c297f3d29be079533db301"
OLD_SHORT = "4fde185a"
NEW_SHORT = "c1d1f9f3"
OLD_WORKFLOW = ".github/workflows/wickhunter-wh09-deploy-20260805-v7.yml"
NEW_WORKFLOW = ".github/workflows/wickhunter-wh09-deploy-20260805-v8.yml"


def replace_required(text: str, old: str, new: str, *, minimum: int = 1) -> str:
    count = text.count(old)
    if count < minimum:
        raise SystemExit(f"expected at least {minimum} occurrences of {old!r}, found {count}")
    return text.replace(old, new)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate.py SOURCE OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    text = source.read_text(encoding="utf-8")
    text = replace_required(text, OLD_WORKFLOW, NEW_WORKFLOW, minimum=3)
    text = replace_required(text, OLD_SHA, NEW_SHA, minimum=3)
    text = replace_required(text, OLD_SHORT, NEW_SHORT)
    text = replace_required(text, "v7", "v8")

    required = (
        "name: WickHunter WH09 fresh PAPER deployment v8",
        "group: wickhunter-wh09-deploy-v8",
        f"EXPECTED_BASE_SHA: {NEW_SHA}",
        f"IMPLEMENTATION_SHA: {NEW_SHA}",
        NEW_WORKFLOW,
        "ACTIVATION_NAME: wickhunter-wh09-activation-20260805-v8-c1d1f9f3",
        "BOT_INSTANCE: wickhunter-paper-v8",
        "OPERATOR_CONTAINER: wickhunter-paper-runtime-v8",
        "GATEWAY_CONTAINER: wickhunter-wh09-egress-v8",
        "INTERNAL_NETWORK: wickhunter-wh09-internal-v8",
        f"OPERATOR_IMAGE: local/wickhunter-paper-runtime:sha-{NEW_SHA}",
        f"GATEWAY_IMAGE: local/wickhunter-paper-egress:sha-{NEW_SHA}",
        'state_runner="$RUNNER_STATE_ROOT/wickhunter-paper-runtime/v8"',
        'state_host="$HOST_STATE_ROOT/wickhunter-paper-runtime/v8"',
        'docker network create --internal --subnet "$subnet" "$INTERNAL_NETWORK"',
        'pool = ipaddress.ip_network("172.31.240.0/20")',
        'if any(candidate.overlaps(existing) for existing in occupied):',
        '[[ "$actual_subnet" == "$subnet" ]]',
        'operator = by_name["wickhunter-paper-runtime-v8"]',
        'gateway = by_name["wickhunter-wh09-egress-v8"]',
        '"operator_container": "wickhunter-paper-runtime-v8"',
        '"gateway_container": "wickhunter-wh09-egress-v8"',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"generated workflow missing markers: {missing!r}")

    forbidden = (OLD_WORKFLOW, OLD_SHA, OLD_SHORT, "v7")
    present = [item for item in forbidden if item in text]
    if present:
        raise SystemExit(f"generated workflow retains stale markers: {present!r}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
