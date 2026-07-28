# ASE-00 strict Ruff report

- exit code: `1`

```text
B009 [*] Do not call `getattr` with a constant attribute value. It is not any safer than normal property access.
   --> ai_platform/research/strategy_engine/ase00_adapter.py:545:32
    |
543 |         config_hash: str,
544 |     ) -> FeatureRecord:
545 |         feature_id = cast(str, getattr(reference, "id"))
    |                                ^^^^^^^^^^^^^^^^^^^^^^^^
546 |         timeframe = cast(str, getattr(reference, "timeframe"))
547 |         parameters = cast(dict[str, JsonValue], dict(getattr(reference, "params")))
    |
help: Replace `getattr` with attribute access
    |
544 |     ) -> FeatureRecord:
    -         feature_id = cast(str, getattr(reference, "id"))
545 +         feature_id = cast(str, reference.id)
546 |         timeframe = cast(str, getattr(reference, "timeframe"))
    |

B009 [*] Do not call `getattr` with a constant attribute value. It is not any safer than normal property access.
   --> ai_platform/research/strategy_engine/ase00_adapter.py:546:31
    |
544 |     ) -> FeatureRecord:
545 |         feature_id = cast(str, getattr(reference, "id"))
546 |         timeframe = cast(str, getattr(reference, "timeframe"))
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
547 |         parameters = cast(dict[str, JsonValue], dict(getattr(reference, "params")))
548 |         return make_feature_record(
    |
help: Replace `getattr` with attribute access
    |
545 |         feature_id = cast(str, getattr(reference, "id"))
    -         timeframe = cast(str, getattr(reference, "timeframe"))
546 +         timeframe = cast(str, reference.timeframe)
547 |         parameters = cast(dict[str, JsonValue], dict(getattr(reference, "params")))
    |

B009 [*] Do not call `getattr` with a constant attribute value. It is not any safer than normal property access.
   --> ai_platform/research/strategy_engine/ase00_adapter.py:547:54
    |
545 |         feature_id = cast(str, getattr(reference, "id"))
546 |         timeframe = cast(str, getattr(reference, "timeframe"))
547 |         parameters = cast(dict[str, JsonValue], dict(getattr(reference, "params")))
    |                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
548 |         return make_feature_record(
549 |             feature_id=feature_id,
    |
help: Replace `getattr` with attribute access
    |
546 |         timeframe = cast(str, getattr(reference, "timeframe"))
    -         parameters = cast(dict[str, JsonValue], dict(getattr(reference, "params")))
547 +         parameters = cast(dict[str, JsonValue], dict(reference.params))
548 |         return make_feature_record(
    |

Found 3 errors.
[*] 3 fixable with the `--fix` option.
```
