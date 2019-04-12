FROM docker.oa.com:8080/public/ailab-py3-torch:latest AS dependency

RUN mkdir /wheels

COPY setup.py ./setup.py

RUN pip wheel . --wheel-dir=/wheels


FROM dependency as base

WORKDIR /nes/

COPY --from=dependency /wheels /tmp/wheels

ADD . ./

RUN pip install --no-index --find-links=/tmp/wheels/. .


FROM base AS encoder

ENTRYPOINT ["gnes", "encode"]

FROM base AS indexer

ENTRYPOINT ["gnes", "index"]

FROM base AS proxy

ENTRYPOINT ["gnes", "proxy"]