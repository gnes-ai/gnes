#!/usr/bin/env sh

TEMPLATE="{\"msgtype\": \"markdown\", \"markdown\": {\"content\": \"# $MSG_TITLE\n > $MSG_CONTENT\n\n > 🔗 [$MSG_LINK]($MSG_LINK)\"}}"

echo "$TEMPLATE" | curl -s $BOT_URL -H 'Content-Type: application/json' --data-binary "@-"