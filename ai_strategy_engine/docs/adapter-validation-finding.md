# ASE-00 adapter validation finding

- compileall exit code: `0`
- Ruff exit code: `1`

## compileall

```text

```

## Ruff

```text
F401 [*] `dataclasses.replace` imported but unused
 --> ai_platform/research/strategy_engine/ase00_adapter.py:6:36
  |
4 | import os
5 | from collections.abc import Mapping, Sequence
6 | from dataclasses import dataclass, replace
  |                                    ^^^^^^^
7 | from datetime import UTC, datetime, timedelta
8 | from pathlib import Path
  |
help: Remove unused import: `dataclasses.replace`
  |
5 | from collections.abc import Mapping, Sequence
  - from dataclasses import dataclass, replace
6 + from dataclasses import dataclass
7 | from datetime import UTC, datetime, timedelta
  |

F401 [*] `datetime.UTC` imported but unused
 --> ai_platform/research/strategy_engine/ase00_adapter.py:7:22
  |
5 | from collections.abc import Mapping, Sequence
6 | from dataclasses import dataclass, replace
7 | from datetime import UTC, datetime, timedelta
  |                      ^^^
8 | from pathlib import Path
9 | from typing import Literal, cast
  |
help: Remove unused import: `datetime.UTC`
  |
6 | from dataclasses import dataclass, replace
  - from datetime import UTC, datetime, timedelta
7 + from datetime import datetime, timedelta
8 | from pathlib import Path
  |

Found 2 errors.
[*] 2 fixable with the `--fix` option.

```
