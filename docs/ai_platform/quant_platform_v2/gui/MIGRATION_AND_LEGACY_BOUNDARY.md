# Migration and legacy boundary

## Principle

Do not rewrite the current platform line-by-line. Treat the existing repository as a behavioural reference, dataset/test corpus and source of proven edge cases. Migrate contracts and behaviour deliberately into a clean v2 architecture.

## Freqtrade

Freqtrade is not a required strategic core for v2, but it currently supplies useful battle-tested behaviour and the repository still contains a real Freqtrade execution adapter. Therefore deletion is a migration outcome, not a starting action.

Classify each dependency as:

- already generic/native;
- adapter-only;
- must replace before decommission;
- safe to delete after parity;
- unknown / requires runtime evidence.

Likely legacy value includes exchange/CCXT plumbing, dry-run behaviour, order/position edge cases, fee/precision handling, backtesting/replay conventions and mature operational lessons.

## FreqAI

FreqAI is distinct from the Python ML ecosystem. V2 should preserve the useful ML capabilities while avoiding framework lock-in:

- retain LightGBM, XGBoost, scikit-learn, PyTorch and related libraries as appropriate;
- make datasets, feature schemas, model artifacts, metrics and provenance platform-owned;
- make `BASELINE | CHALLENGER | ACTIVE | ARCHIVED` lifecycle platform-owned;
- keep activation deliberate and attributable;
- use FreqAI only while it still provides missing capability or useful parity/reference coverage.

Removing FreqAI must not mean removing Python ML.

## Current Portal

The existing Portal should be retained during v2 design/bring-up as:

- a behavioural reference;
- a source of workflow and E2E requirements;
- an oracle for already-proven semantics where those semantics remain desired;
- a fallback for features not yet migrated.

Do not make v2 API contracts mirror legacy endpoint shapes unless the product concept genuinely requires it.

## Migration sequence

1. Freeze v2 domain vocabulary and contracts.
2. Build public market-data ingestion and event identity.
3. Build native deterministic simulation and durable decision/outcome storage.
4. Port one WickHunter decision path with causal parity evidence.
5. Build Bot Detail / Decision Inspector against native contracts.
6. Introduce dataset registry and training job contracts.
7. Add Python challenger training/evaluation and model registry.
8. Add AI Lab as an isolated research service.
9. Migrate additional bot/strategy capabilities.
10. Retire individual Freqtrade/FreqAI seams only after no validated consumer needs them.

## Safety

This migration does not authorize real-money exchange execution, private order credentials, withdrawals or live capital. Any such capability remains a separate future owner-approved programme.
