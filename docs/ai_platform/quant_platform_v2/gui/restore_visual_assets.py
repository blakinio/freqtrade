#!/usr/bin/env python3
"""Build and verify the Quant Platform v2 visual archive from committed assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "ASSET_MANIFEST.json"
FIXED_DT = (2026, 8, 26, 0, 0, 0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_archive(output: Path, manifest: dict) -> None:
    members = manifest["reconstructed_archive"]["members"]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for member in members:
            source = HERE / "assets" / member
            info = zipfile.ZipInfo(member, FIXED_DT)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=HERE / "quant-platform-v2-visual-assets-20260827.zip"
    )
    parser.add_argument("--extract", type=Path)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = manifest["reconstructed_archive"]
    by_member = {item["archive_member"]: item for item in manifest["assets"]}
    for member in expected["members"]:
        source = HERE / "assets" / member
        record = by_member[member]
        actual = digest(source)
        if source.stat().st_size != record["size_bytes"] or actual != record["sha256"]:
            raise SystemExit(f"asset integrity mismatch: {member}")
    build_archive(args.output, manifest)
    actual_archive = digest(args.output)
    if args.output.stat().st_size != expected["size_bytes"] or actual_archive != expected["sha256"]:
        raise SystemExit(f"archive integrity mismatch: {actual_archive}")
    with zipfile.ZipFile(args.output) as archive:
        if archive.namelist() != expected["members"]:
            raise SystemExit("archive member ordering mismatch")
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"archive CRC failure: {bad}")
        if len(archive.namelist()) != expected["member_count"]:
            raise SystemExit("archive member count mismatch")
    summary = (
        f"restored {args.output} ({args.output.stat().st_size} bytes, sha256={actual_archive}, "
        f"members={expected['member_count']}, testzip=clean"
    )
    print(summary)
    if args.extract:
        args.extract.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output) as archive:
            archive.extractall(args.extract)
        print(f"extracted to {args.extract}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
