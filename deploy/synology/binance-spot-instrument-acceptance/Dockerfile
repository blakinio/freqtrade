FROM python:3.13-slim-bookworm

ARG SAMPLER_COMMIT

LABEL org.opencontainers.image.title="Binance Spot instrument acceptance persistent sampler" \
      org.opencontainers.image.description="Public-only continuation of the immutable Binance v3 acceptance run on Synology" \
      org.opencontainers.image.revision="${SAMPLER_COMMIT}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ai_platform /app/ai_platform
COPY deploy/synology/binance-spot-instrument-acceptance/healthcheck.py /usr/local/bin/binance-acceptance-healthcheck

RUN printf '%s' "$SAMPLER_COMMIT" | grep -Eq '^[0-9a-fA-F]{40}$' \
    && python -m pip install --no-cache-dir "jsonschema==4.26.0" \
    && printf '%s\n' "$SAMPLER_COMMIT" > /app/SAMPLER_COMMIT \
    && chmod 0444 /app/SAMPLER_COMMIT \
    && chmod 0555 /usr/local/bin/binance-acceptance-healthcheck \
    && chmod -R a-w /app

ENTRYPOINT ["python", "-m", "ai_platform.market_data.binance_spot_instrument_acceptance_daemon"]
