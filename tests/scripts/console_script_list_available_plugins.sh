#!/bin/sh

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# If package_name and repo_path are passed in, pass to list_available_plugins
if [[ "$1" != "" && "$2" != "" ]]; then
    list_available_plugins readers --package_name $1 --repo_path $2
    retval_readers=$?
    list_available_plugins --package_name $1 --repo_path $2
    retval_all=$?
# Otherwise, run all
else
    list_available_plugins readers
    retval_readers=$?

    list_available_plugins
    retval_all=$?
fi
echo "Readers retval: $retval_readers"
echo "All retval: $retval_all"
exit $((retval_readers+retval_all))
