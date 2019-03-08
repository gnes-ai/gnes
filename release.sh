#!/usr/bin/env bash

set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" != "x" ]]; then
  printf "You are not at master branch, exit";
  exit 1;
fi

#$(grep "$VER_TAG" $CLIENT_CODE | sed -n 's/^.*'\''\([^'\'']*\)'\''.*$/\1/p')
VER=$(git tag -l |tail -n1)
printf "current version:\t\e[1;33m$VER\e[0m\n"

VER=$(echo $VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{if(length($NF+1)>length($NF))$(NF-1)++; $NF=sprintf("%0*d", length($NF), ($NF+1)%(10^length($NF))); print}')
echo "bump the version to:\t\e[1;32m$VER\e[0m"

git tag $VER
git push origin --tags
