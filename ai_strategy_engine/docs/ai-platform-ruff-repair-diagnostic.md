# AI Platform Ruff repair diagnostic

- fix exit code: `0`
- check exit code: `0`
- format exit code: `1`

## Fix output
```text
Found 1 error (1 fixed, 0 remaining).
```

## Proposed diff
```diff
diff --git a/ai_platform/portal/control_plane/__init__.py b/ai_platform/portal/control_plane/__init__.py
index cc063f616..0c9426116 100644
--- a/ai_platform/portal/control_plane/__init__.py
+++ b/ai_platform/portal/control_plane/__init__.py
@@ -11,6 +11,7 @@ from ai_platform.portal.control_plane.database import (
 )
 from ai_platform.portal.control_plane.service import ControlPlaneService
 
+
 if TYPE_CHECKING:
     from ai_platform.portal.control_plane.api import create_app as create_app
 
```

## Full check output
```text
All checks passed!
```

## Format check output
```text
Would reformat: ai_platform/research/strategy_engine/ase00_adapter.py
1 file would be reformatted, 426 files already formatted
```
