from ai_platform.freqaimodels.residual_pytorch_m1_instrumentation import (
    ResidualPyTorchM1EvidenceMixin,
)
from ai_platform.freqaimodels.SeededPyTorchMLPRegressor import SeededPyTorchMLPRegressor


class M1SeededPyTorchMLPRegressor(
    ResidualPyTorchM1EvidenceMixin,
    SeededPyTorchMLPRegressor,
):
    """Instrumented seeded MLP comparator for bounded M1 evidence."""
