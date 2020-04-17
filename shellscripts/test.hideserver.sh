#!/bin/bash

#
# Usage: ./talk.comm100.sh event="questionAsked" question="自我"
#

SERVER_STAGING="https://.../test/hide/"
SERVER_LOCALHOST="http://localhost:5088/hide"

for arg in "$@"
do
    param=`echo "$arg" | sed s/"=.*"//g`
    value=`echo "$arg" | sed s/".*="//g`

    echo "$param = $value"

    if [ "$param" == "server" ] ; then
        if [ "$value" == "staging" ] ; then
            SERVER="$SERVER_STAGING"
        else
            SERVER="$SERVER_LOCALHOST"
        fi
    fi
done

SERVER="$SERVER_LOCALHOST"

RECORDS_JSON="\"records\":
  [{\"MemberKey\": \"jinping\", \"Name\": \"习近平\"}]
"

DATA="{
  $RECORDS_JSON,
  \"hide_colname\": \"Name\",
  \"is_number_only\": 0,
  \"case_sensitive\": 0,
  \"encrypt_key_b64\": \"U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk=\"
}"

curl -i -X POST \
  -H 'Content-Type: application/json' \
  -d "$DATA" \
  $SERVER
