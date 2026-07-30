FROM python:3.13-slim-bookworm

ARG COLLECTOR_COMMIT

LABEL org.opencontainers.image.title="WickHunter production market evidence collector" \
      org.opencontainers.image.description="Public-only Binance USD-M and Bybit Linear evidence capture for Synology" \
      org.opencontainers.image.revision="${COLLECTOR_COMMIT}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ai_platform /app/ai_platform
COPY deploy/synology/wickhunter-market-evidence/healthcheck.py /usr/local/bin/market-evidence-healthcheck

RUN printf '%s' "$COLLECTOR_COMMIT" | grep -Eq '^[0-9a-fA-F]{40}$' \
    && printf '%s\n' "$COLLECTOR_COMMIT" > /app/COLLECTOR_COMMIT \
    && chmod 0444 /app/COLLECTOR_COMMIT \
    && chmod 0555 /usr/local/bin/market-evidence-healthcheck \
    && chmod -R a-w /app

ENTRYPOINT ["python", "-m", "ai_platform.wickhunter.production_market_evidence_daemon"]
