# ruff: noqa
"""Capture contract compatibility facade."""

from ai_platform.market_data.capture_manifest import CaptureManifest
from ai_platform.market_data.capture_request import CaptureRequest
from ai_platform.market_data.segments import (
    GapMarker,
    SegmentManifest,
    assert_order_book_reconstructible,
)

__all__ = [
    "CaptureManifest",
    "CaptureRequest",
    "GapMarker",
    "SegmentManifest",
    "assert_order_book_reconstructible",
]
