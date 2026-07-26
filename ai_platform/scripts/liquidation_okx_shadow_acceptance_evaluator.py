from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_platform.scripts.liquidation_okx_shadow_acceptance import (
    POLICY_PATH,
    OkxShadowAcceptancePolicy,
    exit_code_for_outcome,
    verify_evidence_package,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Independently verify an OKX shadow acceptance evidence package.",
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    policy = OkxShadowAcceptancePolicy.load(args.policy)
    result = verify_evidence_package(args.run_root, policy=policy)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(exit_code_for_outcome(result.get("outcome")))


if __name__ == "__main__":
    main()
