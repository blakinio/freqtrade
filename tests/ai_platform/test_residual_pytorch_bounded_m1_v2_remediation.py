from __future__ import annotations

import numpy as np
import pandas as pd

from ai_platform.strategies.AiFrozenCandidateStrategyV2 import (
    bounded_symmetric_volume_change,
)


def test_volume_change_is_finite_and_bounded_across_zero_volume() -> None:
    volume = pd.Series([0.0, 0.0, 10.0, 0.0, 5.0, 5.0])
    result = bounded_symmetric_volume_change(volume)

    assert np.isfinite(result.to_numpy(dtype=float)).all()
    assert result.tolist() == [0.0, 0.0, 2.0, -2.0, 2.0, 0.0]
    assert result.between(-2.0, 2.0).all()


def test_volume_change_preserves_direction_and_scale_symmetry() -> None:
    volume = pd.Series([10.0, 30.0, 10.0])
    result = bounded_symmetric_volume_change(volume)

    assert result.iloc[1] == 1.0
    assert result.iloc[2] == -1.0
