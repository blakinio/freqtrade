# WH09 browser v4 bounded repair

Scope is limited to the post-merge browser-only acceptance harness.

Required correction:
- consume the newly introduced `wickhunter-wh09-browser-acceptance-20260820-v4.json` request;
- keep target authorization SHA `eafc198857c90caf89a5920da60ae7661c1061ba` and adoption run `32373954360`;
- make helper approval producer and consumer both require schema version `3`;
- retain URL-safe task-owned USER session tokens;
- retain exact target/harness provenance, real Chromium assertions, secret-free evidence, and exact cleanup;
- no Portal deploy, WH09 redeploy/restart, PAPER/LIVE/model activation, order submission, credentials, adapter, or capital authority.
