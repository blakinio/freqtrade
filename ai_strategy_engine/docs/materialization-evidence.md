# ASE-00 materialization evidence

- status: `complete`
- latest develop SHA merged: `81a45bbae0e7b63655ca5a684fb110c5a03fb4d5`
- required and recovered source ZIP SHA-256: `73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f`
- materialized source tree hash before later ASE-00 integration changes: `c8875a8e812f01604efa14a846324a05511c4fc06d18500c4fe5da6ec65898e4`
- materializer command: `python ai_strategy_engine/materialize_starter.py`
- path traversal protection: implemented by `ai_strategy_engine/materialize_starter.py` and covered by unit tests
- required paths: all present
- update method: ordinary non-force merge of `origin/develop`
- provenance: corrupted bootstrap bytes remain recoverable from commit `ff7ee5be1dc3997669ce7039790221384e08fbe2`; exact corrections are recorded in `docs/deflate-recovery.md`
- bootstrap bundle: removed after exact verified materialization to avoid source duplication
