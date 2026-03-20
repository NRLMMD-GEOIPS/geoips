.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Cache Files Managed by GeoIPS
*****************************
GeoIPS manages a number of different cache files. These are produced to speed
up different processes such as the CLI and plugin loading. These cache files
are managed by GeoIPS and should not be modified or deleted by the user. They
are stored in the ``$GEOIPS_CACHE_DIR`` directory, which is set by the
``GEOIPS_CACHE_DIR`` environment variable. If this variable is not set, the
default directory is determined by ``platformdirs.user_cache_dir("geoips")``.
On Linux and WSL this is typically ``~/.cache/geoips``. On MacOS this is typically
``~/Library/Caches/geoips``.

Currently, two files are managed by GeoIPS (more planned in the near future):

- ``cmd_instructions.json`` contains information about CLI commands and their
  descriptions.
- ``alias_mapping.json`` contains information mapping CLI command aliases to
  their full command names.

In the near future, we plan to move the plugin registry files to the cache
directory as well.