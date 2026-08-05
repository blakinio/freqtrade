from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(".github/workflows/wickhunter-wh09-deploy-20260804-v2.yml")
OLD_BASE = "b417d07424136a480785a2ae06e868cfefc96390"
NEW_BASE = "47b917812b96c0f03a18ff7d9d50cddeb8700a72"
OLD_IMPLEMENTATION = "9a9972a8db27e8dcd6672dbbf6b80a34a03b8cd7"
NEW_IMPLEMENTATION = "47b917812b96c0f03a18ff7d9d50cddeb8700a72"


def replace_exact(text: str, old: str, new: str, *, expected: int) -> str:
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"expected {expected} occurrences of {old!r}, found {count}")
    return text.replace(old, new)


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    text = replace_exact(text, OLD_BASE, NEW_BASE, expected=1)
    text = replace_exact(text, OLD_IMPLEMENTATION, NEW_IMPLEMENTATION, expected=3)
    text = replace_exact(text, "-v4-9a9972a8", "-v5-47b91781", expected=1)
    text = replace_exact(text, "v4", "v5", expected=13)

    required = (
        "name: WickHunter WH09 fresh PAPER deployment v5",
        "group: wickhunter-wh09-deploy-v5",
        f"EXPECTED_BASE_SHA: {NEW_BASE}",
        f"IMPLEMENTATION_SHA: {NEW_IMPLEMENTATION}",
        "ACTIVATION_NAME: wickhunter-wh09-activation-20260805-v5-47b91781",
        "BOT_INSTANCE: wickhunter-paper-v5",
        "OPERATOR_CONTAINER: wickhunter-paper-runtime-v5",
        "GATEWAY_CONTAINER: wickhunter-wh09-egress-v5",
        "INTERNAL_NETWORK: wickhunter-wh09-internal-v5",
        f"OPERATOR_IMAGE: local/wickhunter-paper-runtime:sha-{NEW_IMPLEMENTATION}",
        f"GATEWAY_IMAGE: local/wickhunter-paper-egress:sha-{NEW_IMPLEMENTATION}",
        'state_runner="$RUNNER_STATE_ROOT/wickhunter-paper-runtime/v5"',
        'state_host="$HOST_STATE_ROOT/wickhunter-paper-runtime/v5"',
        'operator = by_name["wickhunter-paper-runtime-v5"]',
        'gateway = by_name["wickhunter-wh09-egress-v5"]',
        '"operator_container": "wickhunter-paper-runtime-v5"',
        '"gateway_container": "wickhunter-wh09-egress-v5"',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"repaired workflow is missing required markers: {missing!r}")
    if OLD_BASE in text or OLD_IMPLEMENTATION in text or "v4" in text:
        raise SystemExit("stale v4 deployment identity remains")

    WORKFLOW.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
