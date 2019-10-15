FROM gnes/build-base:latest AS dependency

ARG VCS_REF
ARG BUILD_DATE

LABEL maintainer="team@gnes.ai" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/gnes-ai/gnes/commit/$VCS_REF" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="GNES is Generic Nerual Elastic Search"

WORKDIR /gnes/

COPY setup.py ./setup.py

RUN python -c "import distutils.core;s=distutils.core.run_setup('setup.py').install_requires;f=open('requirements_tmp.txt', 'w');[f.write(v+'\n') for v in s];f.close()" && cat requirements_tmp.txt

RUN pip --no-cache-dir install -r requirements_tmp.txt

FROM dependency as base

ADD setup.py MANIFEST.in requirements.txt README.md ./
ADD gnes ./gnes/

RUN pip install cffi==1.12.3 && pip --no-cache-dir install .[all] \
    && rm -rf /tmp/* && rm -rf /gnes

WORKDIR /

ENV GNES_VCS_VERSION=$VCS_REF
ENV GNES_BUILD_DATE=$BUILD_DATE

ENTRYPOINT ["gnes"]