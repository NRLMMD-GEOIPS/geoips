#!/bin/sh

list_available_plugins readers -l info
retval_readers=$?

list_available_plugins
retval_all=$?

exit $(retval_readers+retval_all)