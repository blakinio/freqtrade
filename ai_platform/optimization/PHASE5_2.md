# Phase 5.2 Exit Optimization

Phase 5.2 is a separate research package.

- Frozen entry threshold: `0.006`.
- Training context: `20251201-20260228`.
- Tuning window: `20260301-20260430`.
- Exit parameter only: `exit_prediction_threshold`.
- Hyperopt space only: `sell`.
- Previous holdout `20260501-20260630` is consumed and is not reused.
- A new unseen final window has not been declared.
- Final validation is therefore blocked for this package.

A stable tuning result is stored as research evidence and waits for a newly declared unseen final window. An unstable result is rejected. This package does not run final validation.
