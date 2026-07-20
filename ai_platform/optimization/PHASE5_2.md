# Phase 5.2 Exit Optimization

Phase 5.2 is a completed research package.

- Frozen entry threshold: `0.006`.
- Selected stable exit threshold: `-0.009`.
- Training context: `20251201-20260228`.
- Tuning window: `20260301-20260430`.
- Exit parameter only: `exit_prediction_threshold`.
- Hyperopt space only: `sell`.
- Previous holdout `20260501-20260630` is consumed and is not reused.
- Stable Phase 5.2 evidence is stored in `ai_platform/evidence/phase5-exit-thresholds-v1.json`.
- A new prospective final holdout is declared separately in `ai_platform/validation/final-holdout-v2-declaration.json` as `20260801-20260930`.
- The new holdout was declared before its start and does not overlap the consumed holdout.
- Final validation is not authorized by this package or by the holdout declaration.
- Final validation must be prepared as a separate work package and must not run before the declared holdout window is complete and available.
- No further tuning is allowed from the future final holdout result.
- Promotion and live trading remain disallowed.

The frozen parameter set for the future separate final-validation package is `entry_prediction_threshold=0.006` and `exit_prediction_threshold=-0.009`.
