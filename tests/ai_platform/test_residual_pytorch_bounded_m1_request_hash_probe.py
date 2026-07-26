from __future__ import annotations

import json
import unittest

from ai_platform.scripts.residual_pytorch_bounded_m1_run_request import canonical_run_request


class ResidualPyTorchBoundedM1RequestHashProbe(unittest.TestCase):
    def test_emit_canonical_hash_bindings(self) -> None:
        request = canonical_run_request()
        bindings = {
            "contract_sha256": request["contract_sha256"],
            "strategy_sha256": request["strategy_sha256"],
            "instrumentation_sha256": request["instrumentation_sha256"],
            "audit_track": request["audit_track"],
            "tracks": request["tracks"],
        }
        self.fail("CANONICAL_HASH_BINDINGS\n" + json.dumps(bindings, indent=2, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
