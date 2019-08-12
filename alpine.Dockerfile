FROM python:3.7.4-alpine AS dependency

WORKDIR /gnes/

COPY setup.py ./setup.py

RUN apk add --no-cache \
            --virtual=.build-dependencies \
            g++ gfortran file binutils \
            musl-dev python3-dev py-pgen cython openblas-dev && \
    apk add libstdc++ openblas && \
    ln -s locale.h /usr/include/xlocale.h && \
    python -c "import distutils.core;s=distutils.core.run_setup('setup.py').install_requires;f=open('requirements_tmp.txt', 'w');[f.write(v+'\n') for v in s];f.close()" && \
    cat requirements_tmp.txt && \
    pip install --no-cache-dir --compile -r requirements_tmp.txt && \
    rm -r /root/.cache && \
    find /usr/lib/python3.*/ -name 'tests' -exec rm -r '{}' + && \
    find /usr/lib/python3.*/site-packages/ -name '*.so' -print -exec sh -c 'file "{}" | grep -q "not stripped" && strip -s "{}"' \; && \
    rm /usr/include/xlocale.h && \
    apk del .build-dependencies

FROM dependency as base

ADD . ./

RUN pip install . --no-cache-dir --compile && \
    && rm -rf /tmp/* \
    && rm -rf /gnes/* \
    && rmdir /gnes

WORKDIR /

ENTRYPOINT ["gnes"]