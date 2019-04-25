#!/usr/bin/env bash

BACK_TITLE='GNES Config'
DLG_HEIGHT=0
DLG_WIDTH=0

if hash "dialog" 2>/dev/null; then
  DIALOG_UI="dialog"
elif hash "whiptail" 2>/dev/null; then
  DIALOG_UI="whiptail"
else
  printf 'no whiptail or dialog found, try apt-get/brew install dialog/whiptail\n' >&2
  printf 'fallback to shell interface without gui support\n' >&2
  DIALOG_UI="shell"
fi

function join_by { local IFS="$1"; shift; echo "$*"; }

function ui.dialog.show_options() {
    ### Arguments
    # TITLE: string
    # SUBTITLE: string
    # OPTIONS: array of string, e.g. ("a", "b")
    # DEFAULT_OPTION: int, 0
    ### Return
    # int, selected options
    tmp_options=()
    id=0
    for each in "${OPTIONS[@]}"
    do
        tmp_options+=($id "${each}")
        let "id++"
    done
    dialog --no-cancel --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --default-item ${DEFAULT_VALUE} --menu "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH} 0 "${tmp_options[@]}"
}

function ui.whiptail.show_options() {
    tmp_options=()
    id=0
    for each in "${OPTIONS[@]}"
    do
        tmp_options+=($id "${each}")
        let "id++"
    done
    whiptail --nocancel --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --default-item ${DEFAULT_VALUE} --menu "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH} 0 "${tmp_options[@]}" 3>&1 1>&2 2>&3
}

function ui.shell.show_options() {
    while true; do
    printf "\e[0;32m▶\e[0m\e[1m ${TITLE} \e[0m \e[2m(default: ${DEFAULT_VALUE})\e[0m\n" 1>&2
    id=0
    tmp_options=()
    for each in "${OPTIONS[@]}"
    do
        printf "\t\e[0;33m($id)\e[0m\t${each}\n" 1>&2
        tmp_options+=("${id}")
        let "id++"
    done
    printf "\e[0;32m▶\e[0m\e[1m Your choice \e[0;33m($(join_by '/' ${tmp_options[@]}))\e[0m :" 1>&2
    read CONT
    if [[ -z "$CONT" ]]; then
      echo ${DEFAULT_VALUE};
      break;
    elif [[ " ${tmp_options[*]} " == *" ${CONT} "* ]]; then
      echo ${CONT};
      break;
    else
      printf "\e[0;31minvalid option '${CONT}', type $(join_by '/' ${tmp_options[@]})\e[0m\n" 1>&2
    fi
    done
}


function ui.dialog.show_yesno() {
    ### Return: 0 for Yes, 1 for No
    dialog --no-cancel --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --yesno "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH};
    if [ "$?" = "1" ]; then
      echo 0;
    else
      echo 1;
    fi
}

function ui.whiptail.show_yesno() {
    whiptail --nocancel --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --yesno "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH} 3>&1 1>&2 2>&3
    if [ "$?" = "1" ]; then
      echo 0;
    else
      echo 1;
    fi
}

function ui.shell.show_yesno() {
    ### Return: 0 for Yes, 1 for No
    while true; do
    printf "\e[0;32m▶\e[0m\e[1m ${TITLE} \e[0m \e[0;33m(y/n)\e[0m \e[2m(default: ${DEFAULT_VALUE})\e[0m :" 1>&2
    read CONT
    if [[ -z "$CONT" ]]; then
        if [ "$DEFAULT_VALUE" = "y" ]; then
          echo 1;
        elif [ "$DEFAULT_VALUE" = "n" ]; then
          echo 0;
        else
          printf "\e[0;31minvalid default value '$DEFAULT_VALUE', type \e[0;33m(y/n)\e[0m\n" 1>&2
        fi
        break;
    elif [ "$CONT" = "y" ]; then
      echo 1;
      break;
    elif [ "$CONT" = "n" ]; then
      echo 0;
      break;
    else
      printf "\e[0;31minvalid value '$CONT', type \e[0;33m(y/n)\e[0m\n" 1>&2
    fi
    done
}

function ui.dialog.show_input() {
    ### Return: string that user input
    dialog --no-cancel --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --inputbox "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH} "${DEFAULT_VALUE}"
}

function ui.whiptail.show_input() {
    whiptail --nocancel --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --inputbox "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH} "${DEFAULT_VALUE}" 3>&1 1>&2 2>&3
}

function ui.shell.show_input() {
    printf "\e[0;32m▶\e[0m\e[1m ${TITLE} \e[0m \e[2m(default: ${DEFAULT_VALUE})\e[0m: " 1>&2
    read CONT
    if [[ -z "$CONT" ]]; then
        echo ${DEFAULT_VALUE}
    else
        echo ${CONT}
    fi
}

function ui.dialog.show_msgbox() {
    ### show a message box to inform user, return nothing
    dialog --no-cancel --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --msgbox "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH}
}

function ui.whiptail.show_msgbox() {
    whiptail --nocancel --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --msgbox "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH}
}

function ui.shell.show_msgbox()
{
  local s b w
  IFS=$'|' s=(${TITLE//$'\\n'/|})
  for l in "${s[@]}"; do
    ((w<${#l})) && { b="$l"; w="${#l}"; }
  done
  tput setaf 3
  printf "\e[0;32m▶\e[0m-${b//?/-}-
| ${b//?/ } |\n" 1>&2
  for l in "${s[@]}"; do
    printf '| \e[1m%*s\e[0m |\n' "-$w" "$l" 1>&2
  done
  printf "| ${b//?/ } |
 -${b//?/-}-\n" 1>&2
    if [ -z "$BLOCK_INPUT" ]; then
        :
    else
        read  -n 1
    fi
}

function ui.show_msgbox() {
    echo $("ui.${DIALOG_UI}.show_msgbox")
}

function ui.show_options() {
    echo $("ui.${DIALOG_UI}.show_options")
}

function ui.show_yesno() {
    echo $("ui.${DIALOG_UI}.show_yesno")
}

function ui.show_input() {
    echo $("ui.${DIALOG_UI}.show_input")
}


function docker_stack_start() {
    # export .env to environment
    env $(cat .env | grep ^[A-Z] | xargs) docker stack deploy --compose-file "$COMPOSE_YAML_PATH" "$GNES_STACK_NAME"
}

VARS="`set -o posix ; set`";


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
        exit
        ;;
   esac
fi

#####
# Config wizard starts here!
# import from a separate file
#####

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

printf "%s\n" "${SCRIPT_VARS[@]}" > $(pwd)/.env
$(TITLE="config is saved at $(pwd)/.env, everything is ready! press enter to start the server";
 TITLE_SHORT='config saved';
 BLOCK_INPUT=0;
 ui.show_msgbox)

docker_stack_start
