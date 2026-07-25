import json

from ai_platform.scripts.rl_v2_lifecycle_seed_robustness_run_request import (
    canonical_rl_v2_lifecycle_seed_robustness_request,
)


def test_emit_canonical_seed_robustness_request() -> None:
    payload = canonical_rl_v2_lifecycle_seed_robustness_request()
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    raise AssertionError(f"CANONICAL_REQUEST_BEGIN\n{rendered}\nCANONICAL_REQUEST_END")
