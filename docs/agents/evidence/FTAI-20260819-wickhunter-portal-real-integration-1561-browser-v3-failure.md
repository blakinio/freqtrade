# WH09 deployed browser v3 failure evidence

Post-merge run: `32419995064`
Synology job: `96591217707`
Harness SHA: `3fc65d7da9511e0bd15c0ab924f6d8dacd1829cc`
Target authorization SHA: `eafc198857c90caf89a5920da60ae7661c1061ba`

The v3 job failed before canonical runtime/browser validation in `Validate dual provenance and deployed target`.
The helper builder wrote `approval.json` with `schema_version: 3`, while the consumer still required `schema_version == 2`.
This is a fail-closed harness-contract mismatch; it did not deploy/restart Portal or WH09 and did not grant trading authority.

A new one-shot v4 request is required because v3 authorization material has been consumed.
The repair must make the helper producer/consumer schema identical and retain the URL-safe synthetic USER session introduced by v3.

Observed after the failed run, WH09 recovered autonomously to `status=healthy`, `runtime_health=healthy`, generation `1674`, with `execution_enabled=false`, `orders_submitted=0`, and `live_capital_authorized=false`.
