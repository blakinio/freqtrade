FROM node:22.23.1-bookworm-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3 AS dependencies

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM node:22.23.1-bookworm-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3 AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1 \
    PORTAL_WEB_DATA_MODE=fixture \
    PORTAL_ENVIRONMENT=test

COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN mkdir -p public \
    && npm run build \
    && ./node_modules/.bin/tsc \
      --noEmit false \
      --target ES2022 \
      --module Node16 \
      --moduleResolution Node16 \
      --types node \
      --skipLibCheck \
      --rootDir . \
      --outDir /tmp/portal-market-evidence-verifier \
      tools/market-evidence-runtime-preflight.ts \
      lib/market-evidence/integrity.ts

FROM node:22.23.1-bookworm-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3 AS node-security-runtime

ARG NODE_VERSION=22.23.2
ARG NODE_LINUX_X64_SHA256=d60acfe00a2932254bb0ad20e01b0d74397a0875595de719654b214f4b03f307
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
    && curl --fail --location --proto '=https' --tlsv1.2 \
        "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
        --output /tmp/node.tar.xz \
    && echo "${NODE_LINUX_X64_SHA256}  /tmp/node.tar.xz" | sha256sum --check --strict \
    && tar --extract --xz --file /tmp/node.tar.xz --directory /tmp \
    && install -m 0755 "/tmp/node-v${NODE_VERSION}-linux-x64/bin/node" /usr/local/bin/node \
    && test "$(node --version)" = "v${NODE_VERSION}" \
    && rm -rf /tmp/node.tar.xz "/tmp/node-v${NODE_VERSION}-linux-x64" \
    && rm -rf /var/lib/apt/lists/*

FROM node:22.23.1-bookworm-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3 AS runtime

COPY --from=node-security-runtime /usr/local/bin/node /usr/local/bin/node
RUN rm -rf \
      /usr/local/lib/node_modules/npm \
      /usr/local/lib/node_modules/corepack \
      /usr/local/bin/npm \
      /usr/local/bin/npx \
      /usr/local/bin/corepack \
      /usr/local/bin/yarn \
      /usr/local/bin/yarnpkg \
    && test "$(node --version)" = "v22.23.2" \
    && printf '%s\n' \
      '#!/bin/sh' \
      'set -eu' \
      'case "${PORTAL_ENVIRONMENT:-}" in' \
      '  staging|production)' \
      '    if [ "${PORTAL_WEB_DATA_MODE:-}" != "api" ]; then' \
      '      echo "fixture Portal data mode is forbidden in staging/production" >&2' \
      '      exit 64' \
      '    fi' \
      '    if [ -z "${PORTAL_CONTROL_PLANE_URL:-}" ]; then' \
      '      echo "PORTAL_CONTROL_PLANE_URL is required in staging/production" >&2' \
      '      exit 64' \
      '    fi' \
      '    if [ "${PORTAL_IDENTITY_FIXTURE_MODE:-disabled}" != "disabled" ]; then' \
      '      echo "identity fixture mode is forbidden in staging/production" >&2' \
      '      exit 64' \
      '    fi' \
      '    ;;' \
      'esac' \
      'exec "$@"' \
      > /usr/local/bin/portal-web-entrypoint \
    && chmod 0555 /usr/local/bin/portal-web-entrypoint

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORTAL_WEB_DATA_MODE=api \
    PORTAL_ENVIRONMENT=staging \
    HOSTNAME=0.0.0.0 \
    PORT=3000

COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /tmp/portal-market-evidence-verifier /usr/local/lib/portal-market-evidence-verifier

USER node

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=4 \
    CMD node -e "fetch('http://127.0.0.1:3000').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"

ENTRYPOINT ["/usr/local/bin/portal-web-entrypoint"]
CMD ["node", "server.js"]
