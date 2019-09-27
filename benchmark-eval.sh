#!/usr/bin/env bash

cd /workspace && rm -rf benchmark && git clone https://github.com/gnes-ai/benchmark.git && cd benchmark

git remote rm origin && git remote add origin https://$GITHUB_USER:$GITHUB_PWD@github.com/gnes-ai/benchmark.git
git config --global user.email "artex.xh@gmail.com" && git config --global user.name "Han Xiao"

export GNES_IMG_TAG=latest-alpine


for EXP_ID in 1 2 3 4 ;
do
    export GNES_BENCHMARK_ID=$EXP_ID
    make pull && make build && make test d=1000 b=10 s=1000000 && make clean
    make wait t=20
done

# faster for debugging CICD
#for EXP_ID in 1 2 ;
#do
#    export GNES_BENCHMARK_ID=$EXP_ID
#    make pull && make build && make test d=100 b=10 s=10 && make clean
#    make wait t=20
#done

cat $BENCHMARK_DIR/.data/history*.json
make run_summary
cat $BENCHMARK_DIR/README.md

git add -u && git status && git commit -m "auto eval the benchmark due to gnes update"
git push --set-upstream origin master