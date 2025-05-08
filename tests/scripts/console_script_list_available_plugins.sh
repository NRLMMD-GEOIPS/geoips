#!/bin/sh

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

list_available_plugins readers -l info
retval_readers=$?

list_available_plugins
retval_all=$?

echo "Readers retval: $retval_readers"
echo "All retval: $retval_all"
exit $((retval_readers+retval_all))