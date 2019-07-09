#!/bin/bash

set -v  # print commands as they're executed
set -e  # fail and exit on any command erroring

function install_swig() {
    # Need SWIG >= 3.0.8
    cd ${HOME}/ext_data &&
        wget https://github.com/swig/swig/archive/rel-3.0.12.tar.gz &&
        tar zxf rel-3.0.12.tar.gz && cd swig-rel-3.0.12 &&
        ./autogen.sh && ./configure 1>/dev/null &&
        make >/dev/null &&
        sudo make install >/dev/null
}

function install_faiss() {
    cd ${HOME}/ext_data &&
        # install faiss from source
        wget https://github.com/facebookresearch/faiss/archive/master.zip  -O temp.zip &&
        unzip temp.zip && rm temp.zip &&
        cd faiss-master &&
        ./configure --without-cuda &&
        make -j 10 &&
        sudo make install &&
        make -C python && cd python &&
        pip install -U .
}

if [ "${TRAVIS_OS_NAME}" == linux ]; then
    install_swig
    install_faiss
fi

