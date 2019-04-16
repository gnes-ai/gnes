#!/usr/bin/env bash

# add this line to import the dialog api
source "./dialog.sh"

bb=$(TITLE='use random port?';
     show_yesno)

printf "2. you choose $bb\n"
