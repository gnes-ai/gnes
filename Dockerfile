FROM gnes/build-base:latest AS dependency

WORKDIR /gnes/

COPY setup.py ./setup.py

RUN python -c "import distutils.core;s=distutils.core.run_setup('setup.py').install_requires;f=open('requirements_tmp.txt', 'w');[f.write(v+'\n') for v in s];f.close()" && cat requirements_tmp.txt

RUN pip --no-cache-dir install -r requirements_tmp.txt

FROM dependency as base

ADD . ./


RUN pip --no-cache-dir install .[all] \
    && rm -rf /tmp/*

WORKDIR /

ENTRYPOINT ["gnes"]