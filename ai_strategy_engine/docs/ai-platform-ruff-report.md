# AI Platform Ruff report

- command: `ruff check ai_platform tests/ai_platform`
- exit code: `1`

```text
I001 [*] Import block is un-sorted or un-formatted
  --> ai_platform/portal/control_plane/__init__.py:1:1
   |
 1 | / from __future__ import annotations
 2 | |
 3 | | from importlib import import_module
 4 | | from typing import TYPE_CHECKING
 5 | |
 6 | | from ai_platform.portal.control_plane.context import RequestContext
 7 | | from ai_platform.portal.control_plane.database import (
 8 | |     build_engine,
 9 | |     build_session_factory,
10 | |     create_schema,
11 | | )
12 | | from ai_platform.portal.control_plane.service import ControlPlaneService
   | |________________________________________________________________________^
13 |
14 |   if TYPE_CHECKING:
   |
help: Organize imports

Found 1 error.
[*] 1 fixable with the `--fix` option.
```
