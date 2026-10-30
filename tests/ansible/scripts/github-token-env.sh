# Source this (POSIX sh) before cloning GeoIPS repositories in a Docker build.
#
# If a GitHub token is given as the BuildKit secret "geoips_private_token", git
# sends it to github.com as an HTTP header set through GIT_CONFIG_* environment
# variables (git >= 2.31). Nothing is written to disk, to an image layer, to the
# image history, or to the cloned repositories' .git/config, and the variables
# only exist for the RUN step that sources this file.
#
#   docker build --target geoips-site --build-arg GEOIPS_USE_PRIVATE_PLUGINS=true \
#       --secret id=geoips_private_token,src=/path/to/token-file .
#
# The token needs read access ("Contents: Read-only") to every repository in
# private_plugin_repos and private_fortran_repos (tests/ansible/inventory).

_geoips_token_file=/run/secrets/geoips_private_token
if [ -s "$_geoips_token_file" ]; then
    _geoips_auth=$(printf 'x-access-token:%s' "$(tr -d ' \r\n' < "$_geoips_token_file")" | base64 | tr -d '\n')
    GIT_CONFIG_COUNT=1
    GIT_CONFIG_KEY_0="http.https://github.com/.extraheader"
    GIT_CONFIG_VALUE_0="AUTHORIZATION: basic ${_geoips_auth}"
    export GIT_CONFIG_COUNT GIT_CONFIG_KEY_0 GIT_CONFIG_VALUE_0
    unset _geoips_auth
    echo "github-token-env.sh: using the geoips_private_token build secret for GitHub"
elif [ "${GEOIPS_USE_PRIVATE_PLUGINS:-false}" = "true" ]; then
    echo "github-token-env.sh: WARNING: GEOIPS_USE_PRIVATE_PLUGINS=true but no" \
         "geoips_private_token build secret; private repositories can only be" \
         "cloned if GEOIPS_REPO_URL needs no credentials."
fi
unset _geoips_token_file
