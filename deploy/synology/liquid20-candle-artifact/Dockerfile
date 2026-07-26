FROM python:3.13-slim-bookworm

ARG CODE_COMMIT

LABEL org.opencontainers.image.title="Liquid20 source-separated candle artifact runtime" \
      org.opencontainers.image.description="Public diagnostic candle evidence runtime for the Synology staging runner" \
      org.opencontainers.image.revision="${CODE_COMMIT}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace

WORKDIR /workspace

COPY . /workspace

RUN printf '%s' "$CODE_COMMIT" | grep -Eq '^[0-9a-f]{40}$' \
    && printf '%s\n' "$CODE_COMMIT" > /workspace/CODE_COMMIT \
    && mkdir -p /output \
    && chown 65534:65534 /output \
    && chmod 0444 /workspace/CODE_COMMIT \
    && chmod -R a-w /workspace

USER 65534:65534
