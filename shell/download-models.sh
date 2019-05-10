#!/usr/bin/env bash

set -e

URL_CHINESE_BERT="https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip"
URL_CHINESE_ELMO="https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/zhs.model.tar.bz2"
URL_GPT="https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/openai_gpt.tar.bz2"
URL_GPT2="https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/openai_gpt2.tar.bz2"
URL_TRANSFORMER_XL="https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/transformer_xl_wt103.tar.bz2"
URL_WORD2VEC="https://gnes-1252847528.cos.ap-guangzhou.myqcloud.com/sgns.wiki.bigram-char.bz2"

curl -s ${URL_CHINESE_BERT} -o temp.zip; unzip temp.zip; rm temp.zip
curl -s ${URL_WORD2VEC} -o tmp.bz2; bzip2 -d tmp.bz2; rm tmp.bz2

tarbz2array=($URL_CHINESE_ELMO $URL_GPT $URL_GPT2 $URL_TRANSFORMER_XL)

for url in "${tarbz2array[@]}"
do
    printf "downloading ${url}\n"
    curl -s ${url} -o tmp.tar.bz2; tar -xjf tmp.tar.bz2; rm tmp.tar.bz2
done

