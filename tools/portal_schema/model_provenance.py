from __future__ import annotations

import json

from ai_platform.portal.control_plane.database import Base
from ai_platform.portal.database.model_registry import load_portal_models


def main() -> int:
    load_portal_models()
    owners: dict[str, list[dict[str, str]]] = {}
    for mapper in Base.registry.mappers:
        table_name = mapper.local_table.name
        owners.setdefault(table_name, []).append(
            {
                "class": mapper.class_.__qualname__,
                "module": mapper.class_.__module__,
            }
        )
    print(json.dumps(dict(sorted(owners.items())), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
