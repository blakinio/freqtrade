#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()
PACKAGE = ROOT / "ai_platform/portal/web/package.json"
DOCKERFILE = ROOT / "deploy/synology/portal/Dockerfile"


def update_package() -> None:
    payload = json.loads(PACKAGE.read_text(encoding="utf-8"))
    dependencies = payload.setdefault("dependencies", {})
    dependencies["sharp"] = "0.35.3"
    PACKAGE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def update_dockerfile() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    marker = (
        "FROM node:22.23.1-bookworm-slim@sha256:"
        "6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3 AS runtime\n\n"
        "WORKDIR /app\n"
    )
    replacement = '''FROM node:22.23.1-bookworm-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3 AS node-security-runtime

ARG NODE_VERSION=22.23.2
ARG NODE_LINUX_X64_SHA256=d60acfe00a2932254bb0ad20e01b0d74397a0875595de719654b214f4b03f307
RUN apt-get update \\
    && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \\
    && curl --fail --location --proto '=https' --tlsv1.2 \\
        "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \\
        --output /tmp/node.tar.xz \\
    && echo "${NODE_LINUX_X64_SHA256}  /tmp/node.tar.xz" | sha256sum --check --strict \\
    && tar --extract --xz --file /tmp/node.tar.xz --directory /tmp \\
    && install -m 0755 "/tmp/node-v${NODE_VERSION}-linux-x64/bin/node" /usr/local/bin/node \\
    && test "$(node --version)" = "v${NODE_VERSION}" \\
    && rm -rf /tmp/node.tar.xz "/tmp/node-v${NODE_VERSION}-linux-x64" \\
    && rm -rf /var/lib/apt/lists/*

FROM node:22.23.1-bookworm-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3 AS runtime

COPY --from=node-security-runtime /usr/local/bin/node /usr/local/bin/node
RUN rm -rf \\
      /usr/local/lib/node_modules/npm \\
      /usr/local/lib/node_modules/corepack \\
      /usr/local/bin/npm \\
      /usr/local/bin/npx \\
      /usr/local/bin/corepack \\
      /usr/local/bin/yarn \\
      /usr/local/bin/yarnpkg \\
    && test "$(node --version)" = "v22.23.2"

WORKDIR /app
'''
    if marker not in text:
        raise SystemExit("expected runtime stage marker not found")
    DOCKERFILE.write_text(text.replace(marker, replacement, 1), encoding="utf-8")


def main() -> None:
    update_package()
    update_dockerfile()


if __name__ == "__main__":
    main()
