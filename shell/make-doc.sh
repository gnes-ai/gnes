#!/usr/bin/env bash

DOC_DIR=docs
GNES_DIR=gnes

sphinx-apidoc -o ${DOC_DIR} ${GNES_DIR} -f
cd ${DOC_DIR} && make html