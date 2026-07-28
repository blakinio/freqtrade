from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from zipfile import ZipFile

EXPECTED_SHA256 = "73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f"


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
            for member in bundle.infolist():
                destination = (root / member.filename).resolve()
                if root not in destination.parents and destination != root:
                    raise SystemExit(f"unsafe archive path: {member.filename}")
            bundle.extractall(root)
    finally:
        archive.unlink(missing_ok=True)

    print(f"Materialized AI Strategy Engine source in {root}")


if __name__ == "__main__":
    main()
