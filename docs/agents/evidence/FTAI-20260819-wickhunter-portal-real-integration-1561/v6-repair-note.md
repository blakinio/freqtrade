# WH09 browser v6 repair note

This branch repairs the final deployed-browser acceptance boundary for Issue #1561 after v5 reached real authenticated Chromium but failed on a stale hard-coded model marker.

Verified v5 failure:
- post-merge run `32476975494` on `develop@e715edb71ef7166c7e740b3adefd4f834b3b9972`;
- Synology job `96756625157`;
- authorization, adoption provenance, helper build/download and dual target provenance passed;
- Chromium reached `/bots` and failed only because the harness required `SHADOW · wh09-h900-v1` while the real Portal renders `SHADOW · <canonical observed_generation.model_version>`;
- zero-capital authority remained enforced;
- failure evidence written only to container `/tmp` could not survive stopped-container tmpfs semantics.

v6:
- preserves accepted target authorization `eafc198857c90caf89a5920da60ae7661c1061ba` and adoption run `32373954360`;
- derives expected mode/model/desired+observed generation from the canonical real control-plane API preflight;
- requires generation convergence before Chromium;
- passes the exact canonical model and generation ids into the browser harness;
- emits a secret-free `WICKHUNTER_EVIDENCE=` JSON line to Docker logs so failure/PASS evidence can be recovered after the browser container stops;
- keeps URL-safe task-owned USER session creation and exact bounded cleanup;
- does not deploy or restart Portal/WH09 and does not authorize PAPER/LIVE/model activation, credentials, orders, withdrawals or real capital.
