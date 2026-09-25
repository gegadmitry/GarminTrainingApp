#!/usr/bin/env sh
set -eu

token_dir=${GARMINTOKENS:-"$HOME/.garminconnect"}

case "$token_dir" in
  "$PWD"|"$PWD"/*)
    printf '%s\n' 'Refusing to store Garmin tokens inside the repository.' >&2
    exit 1
    ;;
esac

umask 077
mkdir -p "$token_dir"
chmod 700 "$token_dir"

exec uvx --python 3.12 \
  --from git+https://github.com/Taxuspt/garmin_mcp \
  garmin-mcp-auth --token-path "$token_dir"