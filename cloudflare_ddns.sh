#!/bin/bash
set -e
python /volume1/scripts/cloudflare_ddns.py "$1" "$2" "$3" "$4"
return $?
# 0 'good' Update successfully
# 1 'nohost' The hostname specified does not exist in this user account
# 2 'notfqdn' The hostname specified is not a fully-qualified domain name
# 3 'badauth' Authenticate failed
# 4 '911' There is a problem or scheduled maintenance on provider side
# 5 'badagent' HTTP method/parameters is not permitted
# 6 'badparam' Bad params
