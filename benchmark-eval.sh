#!/usr/bin/env bash

# prevent duplicate evaluation over multiple CICD machines
if [[ -z "${DO_BENCHMARK}" ]]; then
    printf "\$DO_BENCHMARK not set, exit\n"
    exit 1
fi

cd /workspace && rm -rf benchmark && git clone https://github.com/gnes-ai/benchmark.git && cd benchmark

git remote rm origin && git remote add origin https://$GITHUB_USER:$GITHUB_PWD@github.com/gnes-ai/benchmark.git
git config --global user.email "artex.xh@gmail.com" && git config --global user.name "Han Xiao"

if [[ -z "${DRONE_TAG}" ]]; then
    VER_TAG="latest"
else
    VER_TAG=${DRONE_TAG}
fi

export GNES_IMG_TAG=${VER_TAG}-alpine

docker swarm init
make pull && make build

for EXP_ID in 1 2 3 4 ;
do
    export GNES_BENCHMARK_ID=$EXP_ID
    make clean && make test d=500 b=10 s=1000000 && make clean
    make wait t=40
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

git add -u && git status && git commit -m "auto eval the benchmark due to gnes update (${DRONE_TAG})"
git push --set-upstream origin master