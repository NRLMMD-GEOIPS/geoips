#!/bin/sh
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
#
# initialize.sh — initializeCommand for the GeoIPS dev container.  Runs on the
# HOST before the image is built and the container is created.
#
# devcontainer.json always mounts ~/.geoips/testdata and ~/.geoips/output, because
# its variable substitution is a single non-recursive pass (a default containing
# another ${...} is truncated at the first "}") and mounts cannot be conditional.
# So instead of putting the environment variables in the mount sources, this
# script makes ~/.geoips/testdata and ~/.geoips/output follow them:
#
#   GEOIPS_TESTDATA_DIR set → ~/.geoips/testdata is a symlink to it
#   GEOIPS_OUTDIRS       set → ~/.geoips/output   is a symlink to it
#   unset                    → the plain directory is created
#
# It also writes the GitHub token for the geoips_private_token build secret to
# ~/.geoips/github-token.  That is not read with `--secret ...,env=VAR` because
# `docker build` fails when the variable is unset and devcontainer.json cannot add
# build options conditionally; an empty token file means "public plugins only"
# (github-token-env.sh checks the secret file for content).
#
# Idempotent: safe to run before every container start, and it always exits 0
# unless the home directory is unusable.

set -u

log() { printf '[devcontainer] %s\n' "$*"; }
warn() { printf '[devcontainer] WARNING: %s\n' "$*" >&2; }

if [ -z "${HOME:-}" ]; then
    warn "HOME is not set; cannot prepare ~/.geoips, so the bind mounts will fail."
    exit 0
fi

GEOIPS_HOME="${HOME}/.geoips"

# link_dir <env-var-name> <name>
# Points ~/.geoips/<name> at the value of the environment variable, creating the
# target if needed.  Never destroys data: a non-empty real directory is left
# alone (with a warning) instead of being replaced.
link_dir() {
    _var=$1
    _name=$2
    _link="${GEOIPS_HOME}/${_name}"

    # Indirect expansion: POSIX sh has no ${!var}, and $_var is a literal from
    # the calls below, never user input.
    eval "_target=\${${_var}:-}"
    _target=${_target%/}

    if [ -z "${_target}" ] || [ "${_target}" = "${_link}" ]; then
        mkdir -p "${_link}" || warn "Could not create ${_link}."
        return 0
    fi

    if ! mkdir -p "${_target}"; then
        warn "Could not create ${_target} (from ${_var}); ${_link} is unchanged."
        return 0
    fi

    if [ -L "${_link}" ]; then
        # Already a symlink: retarget it, even if the old target is gone.
        ln -sfn "${_target}" "${_link}" && log "${_link} -> ${_target}"
    elif [ -d "${_link}" ]; then
        if [ -z "$(ls -A "${_link}" 2>/dev/null)" ]; then
            rmdir "${_link}" && ln -s "${_target}" "${_link}" \
                && log "${_link} -> ${_target} (replaced the empty directory)"
        else
            warn "${_link} is a non-empty directory, so it is NOT linked to"
            warn "${_target} (from ${_var}). Move its contents there, or delete"
            warn "it, and re-run; until then the container uses ${_link}."
        fi
    elif [ -e "${_link}" ]; then
        warn "${_link} exists and is not a directory; not linking it to"
        warn "${_target} (from ${_var})."
    else
        ln -s "${_target}" "${_link}" && log "${_link} -> ${_target}"
    fi

    return 0
}

mkdir -p "${GEOIPS_HOME}" || warn "Could not create ${GEOIPS_HOME}."

link_dir GEOIPS_TESTDATA_DIR testdata
link_dir GEOIPS_OUTDIRS output

# ---------------------------------------------------------------------------
# GitHub token for the private plugin build secret
# ---------------------------------------------------------------------------
# GEOIPS_PRIVATE_TOKEN wins; otherwise the token file documented in
# tests/ansible/README.md is reused.  Without either, an empty file is written so
# that the build still runs (public plugins only).
TOKEN_FILE="${GEOIPS_HOME}/github-token"
TOKEN_SOURCE="${HOME}/.config/geoips/github-token"

umask 077
if [ -n "${GEOIPS_PRIVATE_TOKEN:-}" ]; then
    printf '%s' "${GEOIPS_PRIVATE_TOKEN}" > "${TOKEN_FILE}"
    log "Using GEOIPS_PRIVATE_TOKEN for the geoips_private_token build secret."
elif [ -s "${TOKEN_SOURCE}" ]; then
    cat "${TOKEN_SOURCE}" > "${TOKEN_FILE}"
    log "Using ${TOKEN_SOURCE} for the geoips_private_token build secret."
else
    : > "${TOKEN_FILE}"
fi
chmod 600 "${TOKEN_FILE}" 2>/dev/null || true

exit 0
