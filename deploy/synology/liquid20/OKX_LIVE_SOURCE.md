# Liquid20 OKX SWAP live source

## Runtime contract

The persistent `liquid20-live` container starts three independent public market-data sources:

- `binance-usdm`;
- `bybit-linear`;
- `okx-swap`.

OKX uses only the public `liquidation-orders` WebSocket channel and the public SWAP instruments snapshot. The existing accepted OKX parser validates linear USDT swaps and converts contract count through the verified public `ctVal` metadata. The live adapter changes only the emitted Liquid20 source label from the parser identity `okx-usdt-swap` to the runtime identity `okx-swap`.

Each active live run writes:

- `okx-swap.ndjson`;
- `okx-swap-summary.json` with `orders_submitted: 0`;
- `okx-swap-instruments-v1.json` with the public normalization snapshot.

The service does not read or modify accepted historical evidence under `data/runs/`.

## Safety boundary

The live service refuses to start when exchange credentials are present. It has no account endpoint, order route, trading authority, replay, model training, strategy research, leverage, DCA or live-capital authority.

The Portal reads only the existing read-only Liquid20 mount through the same-origin BFF. Browser code does not connect to OKX, the collector or the Synology filesystem.

## Preflight and deployment

Do not deploy from a pull request. Deployment remains limited to the reviewed exact commit after it reaches `develop` and required CI/preflight checks pass.

The existing controlled Synology deployment must prove that all three sources are configured, connected and have advancing source and collector heartbeats. It must preserve the accepted-evidence digest, the non-root runtime identity, the read-only root filesystem, the writable `/data` bind, the existing restart policy and the absence of a Docker socket mount.

After deployment, run the bounded verification step:

```bash
bash deploy/synology/liquid20/verify-okx-live.sh
```

An authenticated same-origin Portal health endpoint may be supplied through `LIQUID20_PORTAL_HEALTH_URL`. Verification requires:

- `okx-swap configured=true`;
- `okx-swap connected=true`;
- an advancing heartbeat;
- the OKX NDJSON and summary files;
- `orders_submitted == 0`;
- healthy Binance and Bybit source state;
- OKX exposed by the Portal when the optional Portal check is enabled.

## Rollback

Use the existing exact-image rollback path. Do not delete or rewrite `data/live/` or accepted historical data. After rollback, verify Binance and Bybit health and allow the prior runtime contract to age naturally. The newer OKX segment remains append-only evidence and is not replayed or imported into models or strategies.
