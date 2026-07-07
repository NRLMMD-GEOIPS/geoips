#!/bin/bash
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
#
# devcontainer-setup.sh — postCreateCommand for the GeoIPS dev container.
#
# 1. Fixes .git for git worktree support so commits work from inside the container.
# 2. Ensures GeoIPS is installed in editable mode.
# 3. Regenerates plugin registries.
#
set -euo pipefail

cd /packages/geoips

# ---------------------------------------------------------------------------
# Git worktree support
# ---------------------------------------------------------------------------
# When the workspace is a git worktree, .git is a FILE containing:
#   gitdir: /absolute/host/path/to/main/.git/worktrees/<name>
# That host path is invalid inside the container.  We remap it to the
# /workspaces-root mount (see devcontainer.json).
#
if [ -f .git ] && grep -q "^gitdir:" .git 2>/dev/null; then
    echo "[devcontainer] Detected git worktree"
    GITDIR_LINE=$(grep "^gitdir:" .git)
    HOST_GITDIR=$(echo "$GITDIR_LINE" | sed 's/^gitdir: //')
    WT_NAME=$(basename "$HOST_GITDIR")

    # Search /workspaces-root for the main repo's .git directory
    REWRITTEN=false
    for REPO_DIR in /workspaces-root/*/; do
        if [ -d "${REPO_DIR}.git" ]; then
            CONTAINER_GITDIR="${REPO_DIR}.git/worktrees/${WT_NAME}"
            echo "gitdir: ${CONTAINER_GITDIR}" > .git
            echo "[devcontainer] Rewrote gitdir → ${CONTAINER_GITDIR}"
            REWRITTEN=true
            break
        fi
    done

    if [ "$REWRITTEN" = false ]; then
        echo "[devcontainer] WARNING: Could not find main repo .git under /workspaces-root"
        echo "[devcontainer] Git operations inside the container may not work."
        echo "[devcontainer] Original gitdir: ${HOST_GITDIR}"
    fi
fi

git config --global --add safe.directory /packages/geoips

# ---------------------------------------------------------------------------
# Editable install + registries
# ---------------------------------------------------------------------------
echo "[devcontainer] Ensuring editable install..."
pip install --no-cache-dir -e '.[doc,test,lint,debug]' 2>/dev/null || true

echo "[devcontainer] Creating plugin registries..."
geoips config create-registries 2>/dev/null || \
    echo "[devcontainer] WARNING: create-registries failed (may need plugins installed first)"

echo "[devcontainer] Setup complete. Welcome to GeoIPS!"
