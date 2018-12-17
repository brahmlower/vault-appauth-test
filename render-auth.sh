#!/usr/bin/env bash
set -e
ROLE_ID=$(vault read auth/approle/role/app/role-id -field=role_id | grep 'role_id' | awk '{print $2}')
ROLE_TOKEN=$(vault token create -policy=ar-token-create -field=token)
AUTH_JSON="{\"role_id\":\"$ROLE_ID\", \"role_token\":\"$ROLE_TOKEN\"}"
echo $AUTH_JSON
echo $AUTH_JSON | mustache - app/settings.yml.mustache app/settings.yml
