#!/bin/bash

set -v  # print commands as they're executed
set -e  # fail and exit on any command erroring

: "${MODEL_DIR:?}"

function donwload_models() {
    # Need SWIG >= 3.0.8
    cd ${MODEL_DIR} \
        && echo "download pretrained bert-cn model ..."
        && wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/zhs.model.tar.bz2 -qO zhs.model.tar.bz2 \
        && tar -xvjf zhs.model.tar.bz2; rm zhs.model.tar.bz2 \
        && echo "download pretrained openai_gpt model ..."
        && wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/openai_gpt.tar.bz2 -qO openai_gpt.tar.bz2 \
        && tar -xvjf openai_gpt.tar.bz2; rm openai_gpt.tar.bz2 \
        && echo "donwload pretrained openai_gpt2 model ..." \
        && https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/openai_gpt2.tar.bz2 -qO openai_gpt2.tar.bz2 \
        && tar -xvjf openai_gpt2.tar.bz2; rm openai_gpt2.tar.bz2 \
        && echo "donwload pretrained transformer_xl_wt103 model ..." \
        && wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/transformer_xl_wt103.tar.bz2 -qO transformer_xl_wt103.tar.bz2 \
        && tar -xvjf transformer_xl_wt103.tar.bz2; rm transformer_xl_wt103.tar.bz2
}

if [ "${TRAVIS_OS_NAME}" == linux ]; then
    donwload_models
fi