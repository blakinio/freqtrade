from ai_platform.strategies.AiDesiredPositionRLResearchStrategy import (
    AiDesiredPositionRLResearchStrategy,
)


class AiDesiredPositionRLLifecycleAlignedResearchStrategy(
    AiDesiredPositionRLResearchStrategy,
):
    """Research-only desired-position variant aligning ROI with active long intent."""

    ignore_roi_if_entry_signal = True
