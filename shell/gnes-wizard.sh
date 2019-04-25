#!/usr/bin/env bash

# add this line to import the dialog api
DIR="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="$PWD"; fi
. "$DIR/_dialog.sh"

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

. "$DIR/_wizard.sh"

######
# Config wizard ends here!
######

SCRIPT_VARS="`grep -vFe "$VARS" <<<"$(set -o posix ; set)" | grep "^[^_]" | grep -v "RANDOM" | grep -v ^VARS=`"; unset VARS;

printf "%s\n" "${SCRIPT_VARS[@]}" > $(pwd)/.env
$(TITLE="config is saved at $(pwd)/.env, everything is ready! press enter to start the server";
 TITLE_SHORT='config saved';
 BLOCK_INPUT=0;
 ui.show_msgbox)

exit
docker_stack_start