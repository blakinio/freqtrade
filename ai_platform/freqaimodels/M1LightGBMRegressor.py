from ai_platform.freqaimodels.residual_pytorch_m1_instrumentation import (
    ResidualPyTorchM1EvidenceMixin,
)
from freqtrade.freqai.prediction_models.LightGBMRegressor import LightGBMRegressor


class M1LightGBMRegressor(ResidualPyTorchM1EvidenceMixin, LightGBMRegressor):
    """Instrumented frozen LightGBM comparator for bounded M1 evidence."""
