#!/bin/bash

set -v  # print commands as they're executed
set -e  # fail and exit on any command erroring


: "${TENSORFLOW_VERSION:?}"
: "${TENSORFLOW_ARCH:?}"
: "${TORCH_VERSION:?}"
: "${TORCH_ARCH:?}"


# Install TensorFlow
pip install https://storage.googleapis.com/tensorflow/linux/${TENSORFLOW_ARCH}/tensorflow-${TENSORFLOW_VERSION}-cp36-cp36m-linux_x86_64.whl
# Install Torch
pip install https://download.pytorch.org/whl/${TORCH_ARCH}/torch-${TORCH_VERSION}-cp36-cp36m-linux_x86_64.whl