# WickHunter WH-09 v13 preflight and early-fail procedure

This procedure is a gate before a fresh canonical WH-09 prospective PAPER activation. It does
not produce acceptance evidence and must not reuse or backfill the sealed v12 journal.

## Safety boundary

The preflight is PAPER-only. It must use the exact candidate and exact merged operator image,
but a dedicated temporary activation, a dedicated empty journal, and a dedicated operator-state
directory. It must not have exchange credentials, an order adapter, execution authority,
automatic promotion, protected-holdout access, submitted orders, or live-capital authority.

Do not point a preflight run at the canonical v13 acceptance journal.

The request must derive the exact Liquid20 reader GID from the mounted live root (for example
`stat -c %g "$LIQUID20_LIVE_HOST"`), verify that it is numeric and matches the Liquid20 data
boundary, and add only that GID as a supplementary group to the `65532:65532` operator. Do not
make Liquid20 files world-readable and do not use group `0` unless it is the verified live-root GID.

## Burn-in gate

The container entrypoint is the restart-safe runtime supervisor. The deployment defaults are:

- cadence: 120 seconds;
- maximum source age: 300 seconds;
- maximum attempts per cycle: 3;
- retry delay: 5 seconds;
- canonical continuous mode: `SUPERVISOR_CYCLES=0`.

For a bounded staging burn-in set `SUPERVISOR_CYCLES=5`. Five successful cycles prove the
exact image can repeatedly read the real Liquid20 boundary, including atomically republished
`live-state-v1.json`, fetch the allowlisted public market inputs, execute the candidate PAPER
iteration, persist journal generations, update health, and persist supervisor telemetry.

A burn-in is PASS only when all of the following are true:

1. the exact image exits zero after all requested cycles;
2. `/runtime/operator/health.json` is healthy and passes the container healthcheck;
3. `/runtime/operator/cycle-telemetry.json` verifies its self-hash and contains one successful
   record for every burn-in cycle;
4. any transient failure is bounded, visible in telemetry, and recovered within at most three
   attempts;
5. the temporary journal is contiguous and contains the successful burn-in generations;
6. no `/runtime/operator/early-fail.json` exists;
7. source freshness remains within 300 seconds and the observed snapshot gaps remain within the
   canonical 1,800,000 ms ceiling;
8. the operator retains primary identity `65532:65532`, its only Liquid20 read authority is the
   verified supplementary live-root GID, and the Liquid20 mount remains read-only;
9. every zero-authority field remains false and `orders_submitted` remains zero.

Any non-retryable runtime/service integrity failure fails the burn-in immediately. Retry is
limited to operator-level data/market iteration failures; it never weakens journal, activation,
binding, or authority validation.

## Early-fail behavior during the canonical window

The supervisor verifies the journal before every attempt. If an already persisted pair of
snapshots is separated by more than 1,800,000 ms, or the elapsed time since the latest persisted
snapshot exceeds that ceiling, the acceptance window can no longer recover.

At that point the supervisor:

1. writes immutable, self-hashed `/runtime/operator/early-fail.json`;
2. publishes fail-closed operator health;
3. stops making further PAPER iterations for that run;
4. exits non-zero when running in a bounded preflight.

A valid existing sentinel is also honored after restart. This prevents waiting until the end of
the prospective window to discover a gap that had already made the run invalid.

The watchdog intentionally does not early-fail missing `allowed` decisions, risk rejections,
parity, or safety exercises while the window can still satisfy them. Those acceptance facts must
remain genuine; the supervisor never manufactures strategy decisions or acceptance evidence.

## Safety-exercise gate

Before the canonical v13 activation, use a separately reviewed PAPER staging request to prove the
four canonical exercise paths:

- circuit breaker;
- model drift;
- restart recovery;
- stale source.

Exercise evidence must be produced from an actual journaled snapshot and persisted through
`CandidatePaperRuntimeService.record_exercise()`. The procedure must prove the expected
fail-closed reason and subsequent state recovery. Synthetic decision counts, fabricated
snapshot IDs, copied v12 evidence, credentials, orders, and live-capital access are forbidden.

## Canonical activation gate

Publish the fresh canonical v13 activation only after:

1. PR #1320 is merged at a terminal-green exact head;
2. the exact merged image passes build/inspect and the bounded burn-in above on
   `freqtrade-synology-staging`;
3. all four safety-exercise paths have passed the separately reviewed PAPER staging procedure;
4. the canonical journal and operator-state roots are new and empty;
5. the deployment request records the exact image digest, operator commit, candidate identity,
   activation identity, journal identity, verified Liquid20 reader GID, and zero-authority proof.

Only then start the prospective WH-09 acceptance clock.
