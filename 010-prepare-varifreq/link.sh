#!/usr/bin/env bash
set -euo pipefail

TARGET="$1"
DIR_SPECIFICEXP="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

source "$DIR_SPECIFICEXP/../link.sh" "$@"
