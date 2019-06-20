#!/bin/bash

set -v  # print commands as they're executed
set -e  # fail and exit on any command erroring

: "${MODEL_DIR:?}"

function donwload_models() {
    cd ${MODEL_DIR}

    if [ ! -f chinese_L-12_H-768_A-12.zip ]; then
        echo "download pretrained bert-chinese_L-12_H-768_A-12 model ..."
        wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip -qO chinese_L-12_H-768_A-12.zip
        unzip chinese_L-12_H-768_A-12.zip
    fi

    if [ ! -f zhs.model.tar.bz2 ]; then
        echo "download pretrained ELMO-zhs model ..."
        wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/zhs.model.tar.bz2 -qO zhs.model.tar.bz2
        tar -xvjf zhs.model.tar.bz2
    fi

    if [ ! -f openai_gpt.tar.bz2 ]; then
        echo "download pretrained openai_gpt model ..."
        wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/openai_gpt.tar.bz2 -qO openai_gpt.tar.bz2
        tar -xvjf openai_gpt.tar.bz2
    fi

    if [ ! -f openai_gpt2.tar.bz2 ]; then
        echo "donwload pretrained openai_gpt2 model ..."
        wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/openai_gpt2.tar.bz2 -qO openai_gpt2.tar.bz2
        tar -xvjf openai_gpt2.tar.bz2
    fi

    if [ ! -f openai_gpt2.tar.bz2 ]; then
        echo "donwload pretrained transformer_xl_wt103 model ..."
        wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/transformer_xl_wt103.tar.bz2 -qO transformer_xl_wt103.tar.bz2
        tar -xvjf transformer_xl_wt103.tar.bz2
    fi

    if [ ! -f sgns.wiki.bigram-char.sample ]; then
        wget https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/sgns.wiki.bigram-char.sample -q0 sgns.wiki.bigram-char.sample
    fi
}

if [ "${TRAVIS_OS_NAME}" == linux ]; then
    donwload_models
fi