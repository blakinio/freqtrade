from pathlib import Path

from ai_platform.portal.execution.driver import DockerHostCapabilityProbe


def test_empty_proc_swaps_is_verified_no_swap(tmp_path: Path) -> None:
    proc_swaps = tmp_path / "swaps"
    proc_swaps.write_text("", encoding="utf-8")

    probe = DockerHostCapabilityProbe(proc_swaps_path=proc_swaps)

    assert probe._host_swap_disabled() is True


def test_malformed_proc_swaps_is_not_trusted(tmp_path: Path) -> None:
    proc_swaps = tmp_path / "swaps"
    proc_swaps.write_text("unexpected content\n", encoding="utf-8")

    probe = DockerHostCapabilityProbe(proc_swaps_path=proc_swaps)

    assert probe._host_swap_disabled() is False


def test_unreadable_proc_swaps_is_not_trusted(tmp_path: Path) -> None:
    probe = DockerHostCapabilityProbe(proc_swaps_path=tmp_path / "missing")

    assert probe._host_swap_disabled() is False
