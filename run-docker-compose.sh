#!/bin/env bash

set -e

SCRIPT_PATH="$(dirname $0)"
# LOGLEVEL=debug
# 
# LOGLEVEL=$( tr '[a-z]' '[A-Z]')

NC=$(tput sgr0)
RED=$(tput setaf 1)
GRN=$(tput setaf 2)
YLW=$(tput setaf 3)
BLU=$(tput setaf 4)

NOW=$(date +"%D %T")

log () {
    loglevel=$1
    msg="${@:2}"

    if [[ $loglevel == DEBUG ]]; then
        color=$BLU
    elif [[ $loglevel == INFO ]]; then
        color=$GRN
    elif [[ $loglevel == WARN ]]; then
        color=$YLW
    elif [[ $loglevel == ERROR ]]; then
        color=$RED
    else
        printf "%s%s%s: %s - %s" "$RED" "ERROR" "$NC" "$NOW" "Bad log level \"$loglevel\""
    fi

    while IFS= read -r line; do
        printf "%s%-6s%s %s - %s\n" "$color" "$loglevel:" "$NC" "$NOW" "$line"
    done <<< "${msg}"
}

debug () {
    msg="${@:1}"
    log "DEBUG" "$msg"
}

info () {
    msg="${@:1}"
    log "INFO" "$msg"
}

warn () {
    msg="${@:1}"
    log "WARN" "$msg"
}

error () {
    msg="${@:1}"
    log "ERROR" "$msg"
}

ensure_dir () {
    dir="$1"
    debug "Checking for $1"
    if [[ ! -d "$1" ]]; then
        info "Creating $1"
        mkdir -p "$1"
        debug "Successfully created $1"
    else
        debug "Directory exists: $1"
    fi
}

config_geoips=$SCRIPT_PATH/setup/config_geoips
if [[ ! -f $config_geoips ]]; then
    error "Cannot find $(basename $config_geoips) in $(dirname $config_geoips)"
else
    debug "Sourcing $config_geoips"
    debug "$(source $SCRIPT_PATH/setup/config_geoips)"
fi

ensure_dir "$GEOIPS_DEPENDENCIES_DIR"
ensure_dir "$GEOIPS_TESTDATA_DIR"
ensure_dir "$GEOIPS_OUTDIRS"

dc_file=${SCRIPT_PATH}/docker-compose.yml
if [[ ! -f $dc_file ]]; then
    error "Cannot find $(basename $dc_file) in $(dirname $dc_file)"
else
    debug "Calling docker-compose up with $dc_file"
    USER_ID=$(id -u ${USER}) GROUP_ID=$(id -g ${USER}) docker-compose up -f $dc_file
fi