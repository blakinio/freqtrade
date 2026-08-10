ARG FREQTRADE_BASE_IMAGE
FROM ${FREQTRADE_BASE_IMAGE}

USER root
RUN gpasswd -d ftuser sudo \
    && sed -i '\|^ftuser ALL=(ALL) NOPASSWD: /bin/chown$|d' /etc/sudoers \
    && rm -f /usr/bin/sudo /usr/bin/sudoedit \
    && ! id -nG ftuser | tr ' ' '\n' | grep -qx sudo \
    && ! grep -Eq '^ftuser .*NOPASSWD' /etc/sudoers

USER ftuser
ENTRYPOINT ["freqtrade"]
CMD ["trade"]
