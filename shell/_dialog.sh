#!/usr/bin/env bash

BACK_TITLE="GNES Config Wizard [wizard version: ${WIZARD_VERSION} GNES build: ${WIZARD_BUILD}]"
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
DIALOG_UI="shell"
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
    whiptail --nocancel --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --msgbox "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH} 3>&1 1>&2 2>&3
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

