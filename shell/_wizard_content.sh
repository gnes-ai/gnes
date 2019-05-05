#!/usr/bin/env bash

### ALL VARIABLES in this script will be automatically exported
### if you dont want to export a variable, start the variable name with "_"

### 1. Set docker image source
_DOCKER_IMG_URL=$(TITLE="select your docker image source from the list:";
                 TITLE_SHORT="docker image source";
                 OPTIONS=("ccr.ccs.tencentyun.com/gnes/aipd-gnes"
                          "docker.oa.com/public/aipd-gnes"
                          "other source")
                 DEFAULT_VALUE=0;
                 ui.show_options)

DOCKER_IMG_URL=""
case "$_DOCKER_IMG_URL" in
    0)
        DOCKER_IMG_URL="ccr.ccs.tencentyun.com/gnes/aipd-gnes";;
    1)
        DOCKER_IMG_URL="docker.oa.com/public/aipd-gnes";;
    2)
        DOCKER_IMG_URL=$(TITLE="what is the URL of your image source";
                         TITLE_SHORT="URL of image";
                         DEFAULT_VALUE="";
                         ui.show_input);;
esac

### 2. Set docker image build version

BUILD_ID=$(TITLE="what is the build version of your image";
           TITLE_SHORT="build version";
           DEFAULT_VALUE="master";
           ui.show_input)

### 3. Set all ports
HOST_PORT_IN=$(TITLE="please specify an incoming port of your service, client will send data to this port";
               TITLE_SHORT="set port in";
               DEFAULT_VALUE="8598";
               ui.show_input)
HOST_PORT_OUT=$(TITLE="please specify an outgoing port of your service, client will receive data from this port";
               TITLE_SHORT="set port out";
               DEFAULT_VALUE="8599";
               ui.show_input)

# these random port need no UI config
INCOME_PROXY_OUT=$RANDOM
MIDDLEMAN_PROXY_IN=$RANDOM
MIDDLEMAN_PROXY_OUT=$RANDOM
OUTGOING_PROXY_IN=$RANDOM

### 4. Set all dirs

_DOWNLOAD_PRETRAINED_GNES=$(TITLE="do you have a pretrained GNES model downloaded?";
                            TITLE_SHORT="pretrained GNES";
                            DEFAULT_VALUE="n";
                            ui.show_yesno)
case "$_DOWNLOAD_PRETRAINED_GNES" in
0)
    _PRETRAINED_GNES_URL=$(TITLE="what is the URL of the pretrained GNES?";
                            TITLE_SHORT="URL of pretrained GNES";
                            DEFAULT_VALUE="https://transfer.sh/ojW1e/";
                            ui.show_input)
    curl -s ${_PRETRAINED_GNES_URL} -o temp.zip; unzip temp.zip; rm temp.zip
    ;;
1)
    ;;
esac


MODEL_DIR=$(TITLE="where is the folder path for pretrained models?";
            TITLE_SHORT="external folder";
            DEFAULT_VALUE="$(pwd)";
            ui.show_input)

OUTPUT_DIR=$(TITLE="where is the folder path for storing the output from the service (e.g. index files, model dumps)?";
            TITLE_SHORT="output folder";
            DEFAULT_VALUE="${MODEL_DIR}/output_data";
            ui.show_input)

#### 5. Set all yamls

ENCODER_YAML_PATH=$(TITLE="what is the YAML path for the encoder?";
                    TITLE_SHORT="encoder yaml";
                    DEFAULT_VALUE="${MODEL_DIR}/encoder.yml";
                    ui.show_input)

INDEXER_YAML_PATH=$(TITLE="what is the YAML path for the indexer?";
                    TITLE_SHORT="indexer yaml";
                    DEFAULT_VALUE="${MODEL_DIR}/indexer.yml";
                    ui.show_input)


_COMPOSE_YAML_PATH=$(TITLE="which mode do you want to run GNES in";
                 TITLE_SHORT="select the mode";
                 OPTIONS=("indexing mode: enabling GNES to index new documents"
                          "querying mode: enabling GNES to search for a given query"
                          "training mode (advanced): enabling GNES to train/fine-tune the encoder")
                 DEFAULT_VALUE=0;
                 ui.show_options)

COMPOSE_YAML_PATH=""
case "$_COMPOSE_YAML_PATH" in
    0)
        COMPOSE_YAML_PATH="${MODEL_DIR}/train-compose.yml";;
    1)
        COMPOSE_YAML_PATH="${MODEL_DIR}/index-compose.yml";;
    2)
        COMPOSE_YAML_PATH="${MODEL_DIR}/query-compose.yml";;
esac

#### 6. Final service naming

GNES_STACK_NAME=$(TITLE="please name this service";
                  TITLE_SHORT="naming gnes service";
                  DEFAULT_VALUE="gnes-swarm-${RANDOM}";
                  ui.show_input)

