FROM python:3.7.4-slim-buster AS dependency

WORKDIR /gnes/

COPY setup.py ./setup.py

RUN apt-get update && apt-get install --no-install-recommends -y \
            build-essential g++ gfortran file binutils \
            python3-dev cython libopenblas-dev && \
    ln -s locale.h /usr/include/xlocale.h && \
    python -c "import distutils.core;s=distutils.core.run_setup('setup.py').install_requires;f=open('requirements_tmp.txt', 'w');[f.write(v+'\n') for v in s];f.close()" && \
    cat requirements_tmp.txt && \
    pip install --no-cache-dir --compile -r requirements_tmp.txt && \
    rm -rf /var/lib/apt/lists/* && \
    rm /usr/include/xlocale.h

FROM dependency as base

ADD . ./

RUN pip install . --no-cache-dir --compile && \
    rm -rf /tmp/* && \
    rm -rf /gnes

WORKDIR /

ENTRYPOINT ["gnes"]