#!/usr/bin/env bash

source _dialog.sh

function docker_stack_start() {
    TIMESTAMP=$(date "+%Y%m%d-%H%M%S")
    (. .env && eval "echo \"$(cat ${COMPOSE_YAML_PATH})\"") > "${TIMESTAMP}-compose.yml"
    printf "compose yaml is written to \e[0;32m${TIMESTAMP}-compose.yml\e[0m\n" >&2
    docker stack deploy --with-registry-auth --compose-file "${TIMESTAMP}-compose.yml" "$GNES_STACK_NAME" --with-registry-auth >&2
}

VARS="`set -o posix ; set`";


### 0. Check if there is a .env pre-existed.
if [[ -f ".env" ]]; then
   _USE_PREV_ENV=$(TITLE='find an existing .env file, probably contains all configs already. Do you want to use it?';
                    TITLE_SHORT='found an .env';
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

source _wizard_content.sh

######
# Config wizard ends here!
######

SCRIPT_VARS="`grep -vFe "$VARS" <<<"$(set -o posix ; set)" | grep "^[^_]" | grep -v "RANDOM" | grep -v ^VARS=`"; unset VARS;

printf "%s\n" "${SCRIPT_VARS[@]}" > .env

_=$(TITLE="config is saved at $(pwd)/.env, everything is ready! \npress enter to start the server \nyou can later terminate the service by \"docker stack rm $GNES_STACK_NAME\"";
    TITLE_SHORT="config saved";
    BLOCK_INPUT=0;
    ui.show_msgbox)

docker_stack_start