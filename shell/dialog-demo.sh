#!/usr/bin/env bash

# add this line to import the dialog api
DIR="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="$PWD"; fi
. "$DIR/_dialog.sh"

aa=$(TITLE='select your docker image source from the list:';
     TITLE_SHORT='example of ui.show_options';
     OPTIONS=("docker.oa"
              "Tencent Cloud"
              "official Dockerhub")
     DEFAULT_VALUE=0;
     ui.show_options)

bb=$(TITLE='use random port?';
     TITLE_SHORT='example of ui.show_yesno';
     DEFAULT_VALUE='n';
     ui.show_yesno)

cc=$(TITLE='what is the name of your server';
     TITLE_SHORT='example of ui.show_input';
     DEFAULT_VALUE='test me!';
     ui.show_input)

dd=$(TITLE='this is just a message to inform user\nnote that this block the process';
     TITLE_SHORT='example of ui.show_msgbox';
     BLOCK_INPUT=0;
     ui.show_msgbox)

ee=$(TITLE="1. you choose $aa\n2. you choose $bb\n3. you type $cc\n";
     TITLE_SHORT='example of ui.show_msgbox';
     ui.show_msgbox)
