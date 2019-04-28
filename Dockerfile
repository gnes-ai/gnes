FROM docker.oa.com:8080/public/ailab-py3-torch:latest AS dependency

# Get the protobuf source from GitHub.
RUN mkdir -p /var/local/git
RUN git clone https://github.com/google/protobuf.git /var/local/git/protobuf

# Build the protobuf library statically and install to /tmp/protoc_static.
WORKDIR /var/local/git/protobuf
RUN ./autogen.sh && \
    ./configure --disable-shared --prefix=/tmp/protoc_static \
    LDFLAGS="-lgcc_eh -static-libgcc -static-libstdc++" && \
    make -j12 && make check && make install

# Build the protobuf library dynamically and install to /usr/local.
WORKDIR /var/local/git/protobuf
RUN ./autogen.sh && \
    ./configure --prefix=/usr/local && \
    make -j12 && make check && make install

WORKDIR /nes/

COPY setup.py ./setup.py

RUN python -c "import distutils.core;s=distutils.core.run_setup('setup.py').install_requires;f=open('requirements_tmp.txt', 'w');[f.write(v+'\n') for v in s];f.close()" && cat requirements_tmp.txt

RUN pip install -r requirements_tmp.txt

FROM dependency as base

ADD . ./

RUN pip install .

WORKDIR /

ENTRYPOINT ["gnes"]