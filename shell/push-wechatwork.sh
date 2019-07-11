#!/usr/bin/env bash

set -ex

TEMPLATE="{\"msgtype\": \"markdown\", \"markdown\": {\"content\": \"# $MSG_TITLE\n > $MSG_CONTENT\n\n > 🔗 [View] $MSG_LINK\"}}"

echo $TEMPLATE | curl -s $BOT_URL \
   -H 'Content-Type: application/json' \
   --data-binary "@-"