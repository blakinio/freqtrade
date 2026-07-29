from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from zipfile import ZipFile

EXPECTED_SHA256 = "73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f"


def _safe_extract(bundle: ZipFile, root: Path) -> None:
    resolved_root = root.resolve()
    for member in bundle.infolist():
        destination = (resolved_root / member.filename).resolve()
        if resolved_root not in destination.parents and destination != resolved_root:
            raise SystemExit(f"unsafe archive path: {member.filename}")
    bundle.extractall(resolved_root)


def main() -> None:
    root = Path(__file__).resolve().parent
    parts = sorted((root / "bootstrap").glob("strategy_engine_source.zip.b64.part*"))
    if not parts:
        raise SystemExit("bootstrap archive parts are missing")

    encoded = "".join(part.read_text(encoding="ascii").strip() for part in parts)
    payload = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"archive checksum mismatch: {digest}")

    archive = root / ".strategy_engine_source.zip"
    archive.write_bytes(payload)
    try:
        with ZipFile(archive) as bundle:
            _safe_extract(bundle, root)
    finally:
        archive.unlink(missing_ok=True)

    print(f"Materialized AI Strategy Engine source in {root}")


if __name__ == "__main__":
    main()
