FROM docker:cli AS docker-cli

FROM ghcr.io/actions/actions-runner:latest

USER root

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose

RUN apt-get update \
    && apt-get install -y --no-install-recommends age ca-certificates coreutils curl openssl python3 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/actions-runner-dist /runner /work /var/lib/freqtrade-staging-state \
    && cp -a /home/runner/. /opt/actions-runner-dist/ \
    && chown -R runner:runner \
        /opt/actions-runner-dist \
        /runner \
        /work \
        /var/lib/freqtrade-staging-state

COPY --chown=runner:runner deploy/synology/freqtrade-runner/entrypoint.sh /usr/local/bin/freqtrade-runner-entrypoint
RUN chmod 0755 /usr/local/bin/freqtrade-runner-entrypoint

USER runner
WORKDIR /runner

ENTRYPOINT ["/usr/local/bin/freqtrade-runner-entrypoint"]
