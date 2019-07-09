#!/usr/bin/env bash

set -e

CODE_BASE='gnes/__init__.py'
VER_TAG='__version__ = '
SOURCE_ORIGIN='github'

function escape_slashes {
    sed 's/\//\\\//g'
}

function change_line {
    local OLD_LINE_PATTERN=$1
    local NEW_LINE=$2
    local FILE=$3

    local NEW=$(echo "${NEW_LINE}" | escape_slashes)
    sed -i .bak '/'"${OLD_LINE_PATTERN}"'/s/.*/'"${NEW}"'/' "${FILE}"
    mv "${FILE}.bak" /tmp/
}


function clean_build {
    rm -rf dist
    rm -rf *.egg-info
    rm -rf build
}

function pub_pypi {
    # publish to pypi
    clean_build
    python setup.py sdist bdist_wheel
    twine upload dist/*
    clean_build
}

function pub_gittag {
    git add $CODE_BASE
    git commit -m "bumping version to $VER"
    git push $SOURCE_ORIGIN master
    git tag $VER
    git push $SOURCE_ORIGIN $VER
}

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" != "master" ]]; then
  printf "You are not at master branch, exit\n";
  exit 1;
fi


#$(grep "$VER_TAG" $CLIENT_CODE | sed -n 's/^.*'\''\([^'\'']*\)'\''.*$/\1/p')
VER=$(git tag -l |tail -n1)
printf "current version:\t\e[1;33m$VER\e[0m\n"

VER=$(echo $VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
printf "bump version to:\t\e[1;32m$VER\e[0m\n"

read -p "release this version? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # write back tag to client and server code
    VER_VAL=$VER_TAG"'"${VER#"v"}"'"
    change_line "$VER_TAG" "$VER_VAL" $CODE_BASE
    pub_pypi
    pub_gittag
fi



