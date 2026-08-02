# WickHunter candidate paper risk gate

The deterministic risk engine rejects supervised models unless they are approved. WH-09 requires one narrower exception so an immutable model in the `candidate` state can be evaluated in a read-only simulation before any owner promotion decision.

`WickHunterRiskContext.candidate_paper_validation_authorized` is disabled by default. When explicitly enabled, it removes only the `MODEL_NOT_APPROVED` blocker and only when all of the following remain true:

- the score is a supervised model in the `candidate` state;
- the intent mode is `SHADOW` or `PAPER`;
- every other deterministic risk, freshness, exposure, confidence, drift, circuit-breaker and kill-switch check passes.

The flag does not authorize `RESEARCH`, cannot create a `LIVE_BLOCKED` intent, does not approve or promote a model and introduces no order adapter. Trading credentials, order submission, execution and live capital remain outside the WickHunter paper runtime.
