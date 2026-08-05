import logging
from pathlib import Path
from typing import Any


try:
    from xgboost.callback import TrainingCallback as _TrainingCallback
except ModuleNotFoundError as exc:
    if not (exc.name == "xgboost" or (exc.name or "").startswith("xgboost.")):
        raise

    class _TrainingCallback:  # type: ignore[no-redef]
        """No-op callback base when optional XGBoost is not installed."""


logger = logging.getLogger(__name__)


class BaseTensorboardLogger:
    def __init__(self, logdir: Path, activate: bool = True):
        pass

    def log_scalar(self, tag: str, scalar_value: Any, step: int):
        return

    def close(self):
        return


class BaseTensorBoardCallback(_TrainingCallback):
    def __init__(self, logdir: Path, activate: bool = True):
        pass

    def after_iteration(self, model: Any, epoch: int, evals_log: Any) -> bool:
        return False

    def after_training(self, model: Any) -> Any:
        return model
