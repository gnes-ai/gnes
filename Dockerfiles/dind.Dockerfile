FROM alpine:latest

RUN apk update && \
    apk upgrade && \
    apk --no-cache add curl bash docker openrc && \
    rc-update add docker boot && \
    rm -rf /var/cache/apk/*

CMD ["bash"]