ARG FREQTRADE_BASE_IMAGE
FROM ${FREQTRADE_BASE_IMAGE}

USER root
COPY ai_platform/portal/execution/runtime_image/portal-runtime-quarantine /usr/local/bin/portal-runtime-quarantine
RUN gpasswd -d ftuser sudo \
    && sed -i '\|^ftuser ALL=(ALL) NOPASSWD: /bin/chown$|d' /etc/sudoers \
    && rm -f /usr/bin/sudo /usr/bin/sudoedit \
    && chmod 0555 /usr/local/bin/portal-runtime-quarantine \
    && chown root:root /usr/local/bin/portal-runtime-quarantine \
    && ! id -nG ftuser | tr ' ' '\n' | grep -qx sudo \
    && ! grep -Eq '^ftuser .*NOPASSWD' /etc/sudoers

USER ftuser
ENTRYPOINT ["/usr/local/bin/portal-runtime-quarantine"]
CMD ["freqtrade", "trade"]
