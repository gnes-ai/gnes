#!/usr/bin/env bash

# add this line to import the dialog api
DIR="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="$PWD"; fi
. "$DIR/dialog.sh"

function docker_stack_start() {
    # export .env to environment
    env $(cat .env | grep ^[A-Z] | xargs) docker stack deploy --compose-file "$COMPOSE_YAML_PATH" "$GNES_STACK_NAME"
}

VARS="`set -o posix ; set`";

#####
# Config wizard starts here!
#####

### 0. Check if there is a .env pre-existed.
if [ -f ".env" ]; then
   _USE_PREV_ENV=$(TITLE='find an existing .env file, probably contains all configs already. Do you want to use it?';
                    TITLE_SHORT='example of ui.show_yesno';
                    DEFAULT_VALUE='y';
                    ui.show_yesno)
   case "$_USE_PREV_ENV" in
    0);;
    1)
        docker_stack_start
   esac
fi

### 1. Set docker image source
_DOCKER_IMG_URL=$(TITLE='select your docker image source from the list:';
                 TITLE_SHORT='docker image source';
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
        DOCKER_IMG_URL=$(TITLE='what is the URL of your image source';
                         TITLE_SHORT='URL of image';
                         DEFAULT_VALUE='';
                         ui.show_input);;
esac

### 2. Set docker image build version

BUILD_ID=$(TITLE='what is build version of your image';
           TITLE_SHORT='build version';
           DEFAULT_VALUE='master';
           ui.show_input)

### 3. Set all ports
HOST_PORT_IN=$(TITLE='please specify an incoming port of your service, client will send data to this port';
               TITLE_SHORT='port in';
               DEFAULT_VALUE='8598';
               ui.show_input)
HOST_PORT_OUT=$(TITLE='please specify an outgoing port of your service, client will receive data from this port';
               TITLE_SHORT='port out';
               DEFAULT_VALUE='8599';
               ui.show_input)

INCOME_PROXY_OUT=$RANDOM
MIDDLEMAN_PROXY_IN=$RANDOM
MIDDLEMAN_PROXY_OUT=$RANDOM
OUTGOING_PROXY_IN=$RANDOM

### 4. Set all dirs

MODEL_DIR=$(TITLE='where is the folder path for pretrained models?';
            TITLE_SHORT='external folder';
            DEFAULT_VALUE='/data/ext_models/ext_models/';
            ui.show_input)

OUTPUT_DIR=$(TITLE='where is the folder path for storing output from the service (e.g. index files, model dumps)?';
            TITLE_SHORT='output folder';
            DEFAULT_VALUE="$(pwd)/tmp_data";
            ui.show_input)

#### 5. Set all yamls

ENCODER_YAML_PATH=$(TITLE='what is the YAML path for encoder?';
                    TITLE_SHORT='encoder yaml';
                    DEFAULT_VALUE='/data/madwang/encoder.yml';
                    ui.show_input)

INDEXER_YAML_PATH=$(TITLE='what is the YAML path for indexer?';
                    TITLE_SHORT='indexer yaml';
                    DEFAULT_VALUE='/data/madwang/indexer.yml';
                    ui.show_input)

COMPOSE_YAML_PATH=$(TITLE='what is the YAML path for docker-compose.yml?';
                    TITLE_SHORT='docker-compose.yml';
                    DEFAULT_VALUE="$(pwd)/docker-compose.yml";
                    ui.show_input)

#### 6. Final service naming

GNES_STACK_NAME=$(TITLE='please name this service';
                    TITLE_SHORT='gnes swarm name';
                    DEFAULT_VALUE="gnes-swarm-${RANDOM}";
                    ui.show_input)

######
# Config wizard ends here!
######

SCRIPT_VARS="`grep -vFe "$VARS" <<<"$(set -o posix ; set)" | grep "^[^_]" | grep -v "RANDOM" | grep -v ^VARS=`"; unset VARS;

$(TITLE="here is a summary of all your variables: \n\n${SCRIPT_VARS[@]}";
 TITLE_SHORT='summary';
 BLOCK_INPUT=0;
 ui.show_msgbox)

printf "%s\n" "${SCRIPT_VARS[@]}" > $(pwd)/.env
$(TITLE="config is saved at $(pwd)/.env, everything is ready! press enter to start the server";
 TITLE_SHORT='config saved';
 BLOCK_INPUT=0;
 ui.show_msgbox)

docker_stack_start