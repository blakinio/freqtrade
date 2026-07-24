FROM python:3.13-slim-bookworm

ARG COLLECTOR_COMMIT

LABEL org.opencontainers.image.title="Liquid20 multi-source liquidation collector" \
      org.opencontainers.image.description="Data-only Bybit and Binance liquidation collection for Synology" \
      org.opencontainers.image.revision="${COLLECTOR_COMMIT}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN python -m pip install --no-cache-dir "websockets==16.0"

COPY ai_platform /app/ai_platform
COPY deploy/synology/liquid20/entrypoint.sh /usr/local/bin/liquid20-entrypoint

RUN printf '%s' "$COLLECTOR_COMMIT" | grep -Eq '^[0-9a-fA-F]{40}$' \
    && printf '%s\n' "$COLLECTOR_COMMIT" > /app/COLLECTOR_COMMIT \
    && chmod 0444 /app/COLLECTOR_COMMIT \
    && chmod 0555 /usr/local/bin/liquid20-entrypoint \
    && chmod -R a-w /app

ENTRYPOINT ["/usr/local/bin/liquid20-entrypoint"]
