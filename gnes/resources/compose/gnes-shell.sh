#!/usr/bin/env bash

set -e

trap 'kill $(jobs -p)' EXIT

{{gnes-template}}

wait