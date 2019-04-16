#!/usr/bin/env bash

BACK_TITLE='GNES configuration'
DLG_HEIGHT=15
DLG_WIDTH=50

ui.show_options() {
    ### Arguments
    # TITLE: string
    # SUBTITLE: string
    # OPTIONS: array of string, e.g. ("a", "b")
    # DEFAULT_OPTION: int, 0
    ### Return
    # int, selected options
    dialog --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --default-item ${DEFAULT_OPTION} --menu "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH} 0 "${OPTIONS[@]}"
}

ui.show_yesno() {
    ### Return: 0 for Yes, 1 for No
    dialog --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --yesno "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH};
    echo $?
}

ui.show_input() {
    ### Return: string that user input
    dialog --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --inputbox "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH}
}

ui.show_msgbox() {
    ### show a message box to inform user, return nothing
    dialog --stdout --backtitle "${BACK_TITLE}" --title "${TITLE_SHORT}" --msgbox "${TITLE}" ${DLG_HEIGHT} ${DLG_WIDTH}
}

