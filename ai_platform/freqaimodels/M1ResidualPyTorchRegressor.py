from ai_platform.freqaimodels.residual_pytorch_m1_instrumentation import (
    ResidualPyTorchM1EvidenceMixin,
)
from ai_platform.freqaimodels.ResidualPyTorchRegressor import ResidualPyTorchRegressor


class M1ResidualPyTorchRegressor(
    ResidualPyTorchM1EvidenceMixin,
    ResidualPyTorchRegressor,
):
    """Instrumented residual MLP for bounded M1 evidence."""
