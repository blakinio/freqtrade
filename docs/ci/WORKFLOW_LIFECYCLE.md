# GitHub Actions workflow lifecycle

## Purpose

The checked-in directory `.github/workflows/` is the authoritative current workflow surface. GitHub's Actions API also retains workflow records created by files that existed on earlier commits or temporary branches. A catalog record reported as `active` therefore does not by itself prove that the workflow remains a supported or dispatchable entry point.

The repository keeps two complementary controls:

- `.github/workflow-registry.yaml` registers every current workflow file, its owner, purpose, triggers, permissions, risk class, lifecycle and review date;
- `docs/agents/evidence/FTAI-CI-001/workflow-catalog.json` is a point-in-time inventory of every Actions API record, including current-file presence, latest run, open-PR ownership, classification and retirement result.

## Canonical entry points

The central required pull-request gates are:

- `.github/workflows/ci.yml`;
- `.github/workflows/ci-components.yml`;
- `.github/workflows/zizmor_action.yml` for workflow security analysis.

Reusable component workflows are invoked through the central routing workflows unless their documented contract explicitly permits another trigger.

## Lifecycle classes

Current records are classified as `canonical`, `reusable_component`, `operational_schedule`, `bounded_diagnostic`, `migration_cutover` or `temporary_helper`. A record whose file is absent from the checked-out repository and whose latest run branch is not owned by an open pull request is `historical_deleted`.

A temporary workflow must declare:

- an accountable owner;
- a tracking Issue or pull request;
- an expiry date;
- an exact retirement procedure;
- a review date.

CI fails when a current workflow is absent from the registry, a registry entry has no current file, or a temporary workflow has expired or lacks its retirement contract.

## Safe catalog retirement

Run the catalog tool with an Actions-write token:

```bash
python tools/ci/workflow_catalog.py \
  --repository blakinio/freqtrade \
  --root . \
  --output docs/agents/evidence/FTAI-CI-001/workflow-catalog.json \
  --registry .github/workflow-registry.yaml \
  --retire
```

Retirement is not based on workflow names. The tool disables a record only when all of the following are true:

1. the workflow file is absent from the checked-out repository state;
2. the latest run branch is not the head of an open pull request;
3. the latest run is not queued, requested, waiting, pending or in progress;
4. the API record still reports `active`.

Records owned by open pull requests remain active as bounded diagnostics until those pull requests become terminal. The next inventory run then reclassifies and retires them.

## Change procedure

A workflow change must update the workflow file and registry in the same pull request. New temporary helpers must be removed and disabled before task closeout. Material trigger, permission, schedule, deployment or production changes require the repository's normal security and exact-head CI review; registry metadata never substitutes for implementation evidence.
