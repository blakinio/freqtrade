# ASE-00 Ruff findings

- exit code: `1`

```text
TRY004 Prefer `TypeError` exception for invalid type
  --> tests/unit/test_miyagi_provenance.py:22:13
   |
20 |             names.update(str(value) for value in values)
21 |         else:
22 |             raise AssertionError(f"invalid classification payload: {classification}")
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
23 |     return names
   |

Found 1 error.

```
