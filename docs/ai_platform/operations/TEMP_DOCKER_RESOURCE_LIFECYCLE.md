# Temporary Docker Resource Lifecycle

Temporary Docker containers created by agents, diagnostics, acceptance runs, or bounded operational tasks must be attributable and self-expiring. Persistent Portal services, databases, runners, bot runtimes, datasets, evidence stores, volumes, images, and shared networks are outside this automatic cleanup contract.

## Required labels for automatic cleanup

A container is eligible for automatic cleanup only when all labels below are present and exact:

```text
io.freqtrade.lifecycle=temporary
io.freqtrade.cleanup=auto
io.freqtrade.owner-task=<durable task id>
io.freqtrade.expires-at=<RFC3339 timestamp with timezone>
```

Example:

```bash
docker run --name "ftai-20260817-example-probe" \
  --label io.freqtrade.lifecycle=temporary \
  --label io.freqtrade.cleanup=auto \
  --label io.freqtrade.owner-task=FTAI-20260817-example \
  --label io.freqtrade.expires-at=2026-08-18T00:00:00Z \
  ...
```

The creating task still owns immediate cleanup through shell traps or `if: always()` where practical. The scheduled collector is a recovery mechanism for abandoned stopped resources, not a substitute for normal closeout.

## Automatic collector guardrails

`deploy/synology/task_owned_docker_cleanup.py` removes a container only when:

1. both lifecycle and cleanup opt-in labels match exactly;
2. `owner-task` is non-empty;
3. `expires-at` is valid, timezone-aware RFC3339 and is in the past;
4. the container is not running, paused, or restarting.

The collector uses `docker rm <exact-id>` without `--force` and without volume-removal flags. It does not invoke `docker system prune`, `docker container prune`, image pruning, network pruning, or volume pruning.

Malformed, unlabeled, not-yet-expired, or active resources are reported and retained. A stopped Portal service, database, runner, bot runtime, or other persistent component is never automatically removed merely because it is old or stopped.

## Automation

`.github/workflows/task-owned-docker-cleanup.yml` runs daily on the Synology runner and may also be started manually. Scheduled runs apply cleanup. Manual dispatch defaults to report-only and requires `apply=true` to mutate.

The job emits a JSON report to its log containing evaluated candidates, reasons, removed IDs, and failures. No secret values or container environment values are collected.
