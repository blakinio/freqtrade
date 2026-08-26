#!/usr/bin/env python3
"""Reconstruct the Quant Platform v2 visual reference archive from repository text parts."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "ASSET_MANIFEST.json"
PARTS = HERE / "assets" / "archive_parts"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "quant-platform-v2-visual-assets-20260826.zip")
    parser.add_argument("--extract", type=Path)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = manifest["reconstructed_archive"]
    # Resolve from repository root rather than relying on cwd.
    repo_root = HERE.parents[3]
    part_paths = [repo_root / path for path in expected["parts"]]
    encoded = "".join(path.read_text(encoding="ascii") for path in part_paths)
    payload = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected["sha256"]:
        raise SystemExit(f"archive hash mismatch: {digest} != {expected['sha256']}")
    args.output.write_bytes(payload)
    print(f"restored {args.output} ({len(payload)} bytes, sha256={digest})")
    if args.extract:
        args.extract.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output) as archive:
            archive.extractall(args.extract)
        print(f"extracted to {args.extract}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
