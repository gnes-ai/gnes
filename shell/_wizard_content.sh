### ALL VARIABLES in this script will be automatically exported
### if you dont want to export a variable, start the variable name with "_"

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

# these random port need no UI config
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

COMPOSE_YAML_PATH=$(TITLE='what is the YAML path of your template docker-compose.yml?';
                    TITLE_SHORT='template docker-compose.yml';
                    DEFAULT_VALUE="$(pwd)/docker-compose.yml";
                    ui.show_input)

MY_YAML_PATH=$(TITLE='what is the YAML path of your modified docker-compose.yml?';
               TITLE_SHORT='modified docker-compose.yml';
               DEFAULT_VALUE="$(pwd)/my-docker-compose.yml";
               ui.show_input)


#### 6. Final service naming

GNES_STACK_NAME=$(TITLE='please name this service';
                    TITLE_SHORT='gnes swarm name';
                    DEFAULT_VALUE="gnes-swarm-${RANDOM}";
                    ui.show_input)