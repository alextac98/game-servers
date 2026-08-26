FROM alpine:3.24.1

RUN apk add --no-cache openssh-client-default \
    && addgroup -g 10001 tunnel \
    && adduser -D -H -u 10001 -G tunnel tunnel

COPY --chmod=755 entrypoint.sh /usr/local/bin/tunnel-entrypoint

USER tunnel:tunnel
ENV HOME=/tmp

ENTRYPOINT ["/usr/local/bin/tunnel-entrypoint"]
