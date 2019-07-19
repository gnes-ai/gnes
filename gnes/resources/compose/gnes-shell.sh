#!/usr/bin/env bash

## Prerequirment of this script
## You need to install GNES locally on this local machine
## pip install gnes

set -e

trap 'kill $(jobs -p)' EXIT

{{gnes-template}}

wait