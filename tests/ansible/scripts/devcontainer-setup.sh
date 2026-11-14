#!/bin/bash
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
#
# devcontainer-setup.sh — postCreateCommand for the GeoIPS dev container.
#
# 1. Makes git worktrees usable inside the container without touching the
#    bind-mounted .git file (see below).
# 2. Regenerates plugin registries.
#
# GeoIPS itself is already installed (editable, from the image's `dev` stage) and
# nothing is installed here: `uv pip install --system` wrote to /usr/local, which
# the remote user cannot write to, so a pip run here would shadow that install
# with a second copy in ~/.local.
#
set -euo pipefail

cd /packages/geoips

WORKSPACE=/packages/geoips
WORKSPACES_ROOT=/workspaces-root

# ---------------------------------------------------------------------------
# Git worktree support
# ---------------------------------------------------------------------------
# In a worktree, .git is a FILE on the host containing an absolute host path:
#   gitdir: /host/path/to/main/.git/worktrees/<name>
# That path does not exist inside the container.  The .git file is on the
# bind-mounted host workspace, so it MUST NOT be rewritten: that would leave the
# host worktree pointing at a container-only path.
#
# Instead, materialise the host path inside the container as a symlink to the
# /workspaces-root mount (the host workspace's grandparent, see devcontainer.json):
#   /host/path/to/main  ->  /workspaces-root
# which makes the recorded gitdir resolve as-is.
#
# A plain clone (.git directory) needs none of this.
# ---------------------------------------------------------------------------
if [ -f .git ]; then
    echo "[devcontainer] Detected git worktree"

    HOST_GITDIR=$(sed -n 's/^gitdir:[[:space:]]*//p' .git | head -n 1 | tr -d '\r')

    # A relative gitdir (submodule) resolves inside the workspace already.
    case "${HOST_GITDIR}" in
        /*) ;;
        '') ;;
        *) HOST_GITDIR="${WORKSPACE}/${HOST_GITDIR}" ;;
    esac

    if [ -z "${HOST_GITDIR}" ]; then
        echo "[devcontainer] WARNING: .git has no gitdir line; leaving it alone."
    elif [ -e "${HOST_GITDIR}" ]; then
        echo "[devcontainer] gitdir already resolves: ${HOST_GITDIR}"
    elif [ ! -d "${WORKSPACES_ROOT}" ]; then
        echo "[devcontainer] WARNING: ${WORKSPACES_ROOT} is not mounted, so"
        echo "[devcontainer]          ${HOST_GITDIR} cannot be mapped. Git may not"
        echo "[devcontainer]          work inside the container."
    else
        WT_NAME=$(basename "${HOST_GITDIR}")
        MATCH=""
        FALLBACK=""
        FALLBACK_LEN=0

        # The admin dir of this worktree is <main repo>/.git/worktrees/<name>
        # under the mount.  Its path relative to the mount is the tail of the
        # host path recorded in .git, so that tail identifies the right one when
        # several main repos under /workspaces-root have a worktree of this name.
        while IFS= read -r -d '' CAND; do
            [ -n "${CAND}" ] || continue
            REL=${CAND#"${WORKSPACES_ROOT}"/}
            case "${HOST_GITDIR}" in
                */"${REL}") ;;
                *) continue ;;
            esac

            # Prefer the worktree whose back-link points at a .git inside a
            # directory named like this workspace (i.e. at this workspace).
            if [ -f "${CAND}/gitdir" ]; then
                BACKLINK=$(tr -d '\r\n' < "${CAND}/gitdir")
                case "${BACKLINK}" in
                    */"$(basename "${WORKSPACE}")"/.git)
                        MATCH="${CAND}"
                        break
                        ;;
                esac
            fi

            # Otherwise the longest matching tail wins: a shorter one is another
            # repository that merely ends with the same path components.
            if [ "${#REL}" -gt "${FALLBACK_LEN}" ]; then
                FALLBACK="${CAND}"
                FALLBACK_LEN=${#REL}
            fi
        done < <(find "${WORKSPACES_ROOT}" -maxdepth 6 -type d \
                      -path "*/.git/worktrees/${WT_NAME}" -print0 2>/dev/null)

        [ -n "${MATCH}" ] || MATCH="${FALLBACK}"

        if [ -z "${MATCH}" ]; then
            echo "[devcontainer] WARNING: no ${WT_NAME} worktree admin dir found"
            echo "[devcontainer]          under ${WORKSPACES_ROOT}, so"
            echo "[devcontainer]          ${HOST_GITDIR} stays unresolvable."
            echo "[devcontainer]          Git may not work inside the container;"
            echo "[devcontainer]          the main repo's parent must be mounted at"
            echo "[devcontainer]          ${WORKSPACES_ROOT}."
        else
            REL=${MATCH#"${WORKSPACES_ROOT}"/}
            # Host path of the mount source: the recorded gitdir minus the
            # mount-relative tail.
            HOST_PREFIX=${HOST_GITDIR%"/${REL}"}

            if [ -z "${HOST_PREFIX}" ] || [ "${HOST_PREFIX}" = "/" ]; then
                echo "[devcontainer] WARNING: unexpected gitdir ${HOST_GITDIR};"
                echo "[devcontainer]          not creating a symlink for it."
            elif [ -e "${HOST_PREFIX}" ]; then
                echo "[devcontainer] gitdir reachable via ${HOST_PREFIX}"
            elif sudo mkdir -p "$(dirname "${HOST_PREFIX}")" \
                    && sudo ln -s "${WORKSPACES_ROOT}" "${HOST_PREFIX}"; then
                echo "[devcontainer] Linked ${HOST_PREFIX} -> ${WORKSPACES_ROOT}"
                if [ -d "${HOST_GITDIR}" ] && \
                   [ "$(cd "${HOST_GITDIR}" && pwd -P)" = "$(cd "${MATCH}" && pwd -P)" ]; then
                    echo "[devcontainer] gitdir now resolves: ${HOST_GITDIR}"
                else
                    echo "[devcontainer] WARNING: ${HOST_GITDIR} does not resolve"
                    echo "[devcontainer]          to ${MATCH}; git may not work in"
                    echo "[devcontainer]          the container."
                fi
            else
                echo "[devcontainer] WARNING: could not link ${HOST_PREFIX} ->"
                echo "[devcontainer]          ${WORKSPACES_ROOT}; git may not work"
                echo "[devcontainer]          inside the container."
            fi
        fi
    fi
fi

# Idempotent, and never fatal: `git config` still discovers the repository, which
# fails while a worktree's gitdir is unresolved (warned about above).
if ! git config --global --get-all safe.directory 2>/dev/null \
        | grep -qxF "${WORKSPACE}"; then
    git config --global --add safe.directory "${WORKSPACE}" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Plugin registries
# ---------------------------------------------------------------------------
echo "[devcontainer] Creating plugin registries..."
geoips config create-registries 2>/dev/null || \
    echo "[devcontainer] WARNING: create-registries failed (may need plugins installed first)"

echo "[devcontainer] Setup complete. Welcome to GeoIPS!"
