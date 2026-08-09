FROM python:3.13-slim-bookworm

ARG OPERATOR_COMMIT

LABEL org.opencontainers.image.title="WickHunter WH09 production research runtime" \
      org.opencontainers.image.revision="${OPERATOR_COMMIT}" \
      org.opencontainers.image.source="https://github.com/blakinio/freqtrade"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN test -n "$OPERATOR_COMMIT" \
    && OPERATOR_COMMIT="$OPERATOR_COMMIT" python - <<'PY'
import os
import re

value = os.environ.get("OPERATOR_COMMIT", "")
if re.fullmatch(r"[0-9a-f]{40}", value) is None:
    raise SystemExit("OPERATOR_COMMIT must be an exact lowercase Git SHA")
PY

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 65532 wickhunter \
    && useradd --uid 65532 --gid 65532 --no-create-home --home-dir /nonexistent \
        --shell /usr/sbin/nologin wickhunter

WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir lightgbm==4.6.0 \
    && python -m pip install --no-cache-dir -e /app/ft_client \
    && python -m pip install --no-cache-dir -e /app \
    && python -m compileall -q \
        /app/ai_platform/wickhunter/production_research_runtime.py \
        /app/ai_platform/wickhunter/production_research_runtime_operator.py \
        /app/deploy/synology/wickhunter-production-research-runtime/research_runtime_healthcheck.py \
    && find /app -type d -name __pycache__ -prune -exec rm -rf '{}' + \
    && chown -R root:root /app \
    && chmod -R a-w /app

USER 65532:65532

ENTRYPOINT ["python", "-m", "ai_platform.wickhunter.production_research_runtime_operator"]
