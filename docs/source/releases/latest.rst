Version latest (2024-11-13)
***************************

 * *Bug fix*: Add create_plugin_registries to base_test
 * *Bug fix*: Remove unused noaa aws dataset from base tests
 * *Bug fix*: Fix environment variable substitution
 * *Bug fix*: Change fail state for unit test
 * *Bug fix*: Improved data download and memory management during full install
 * *Bug fix*: Fix dir creation bug on oserror
 * *Refactoring updates*: Share logger object to cli command classes
 * *Enhancement*: Rewrite docs build in python
 * *Enhancement*: Organize imports
 * *Enhancement*: NO TITLE
 * *Enhancement*: Added new geoips list source-names command
 * *Documentation*: Add additional info to ram system install requirements section
 * *Documentation*: Add numpy docstrings and examples to coding standards
 * *Documentation*: Write docstrings for base_paths
 * *Refactor*: Ensure consistent module aliases
 * *Refactor*: Refactor base_paths

Bug fix
=======

Add create_plugin_registries to base_test
-----------------------------------------

create_plugin_registries needs to be run before tests. It is included in full_test.sh, but not in base_test.sh. This
updates base_test.sh to call create_plugin_registries just like full_test.sh

::

     modified: tests/integration_tests/base_install.sh

Bug fix
=======

Remove unused noaa aws dataset from base tests
----------------------------------------------

Removed NOAA AWS dataset from the base tests
because it was unused resulting in a ~6X faster install
(2m 28s -> 24s) and a ~4.25 smaller data footprint (3.8Gb -> 894Mb).

::

     modified: tests/integration_tests/base_install.sh

Bug fix
=======

Fix environment variable substitution
-------------------------------------

Change string operations on env var replacement to use pathlib to fix issue with links

::

     modified: geoips/geoips_utils.py

Bug fix
=======

Change fail state for unit test
-------------------------------

Changed reader unit-test to xfail on missing data rather than fail.

::

     modified: tests/unit_tests_long/plugins/modules/readers/test_readers.py

Bug fix
=======

Improved data download and memory management during full install
----------------------------------------------------------------

Fixes a memory bug by streaming download and decompression instead of storing
in memory.

::

     added: setup/test-data-urls.yaml
     modified: setup/check_system_requirements.sh
     modified: setup/download_test_data.py

Bug fix
=======

Fix dir creation bug on oserror
-------------------------------

Fixes found issue with make_dirs. Previously, if make_dirs was passed a read only directory (eg. ``/read_only``), it
would print:

.. code-block:: bash

    "/read_only: We thought /read_only did not exist, but then it did. "
    "Not trying to make directory",

This is was for anything that could trigger any of these OS Errors:

- OSError
- BlockingIOError
- ChildProcessError
- ConnectionError
- BrokenPipeError
- FileNotFoundError
- InterruptedError
- IsADirectoryError
- NotADirectoryError
- PermissionError
- ProcessLookupError
- TimeoutError

Which is far beyond the FileExistsError that was originally supposed to be caught.

::

     modified: geoips/filenames/base_paths.py

Refactoring updates
===================

Share logger object to cli command classes
------------------------------------------

*From GEOIPS#714: 7-26-24, Discuss how to share LOG attribute in the CLI*

Since we've started developing the GeoIPS CLI, we've known that there was a need to
have a shared logger object among all of the CLI command classes for debugging
purposes and to output basic information to the user if requested. We can now do
this using the '--log-level' / '-log' flag. Depending on the log level set, all
levels that match or are of higher 'order' than the log level provided will be
outputted. This functionality matches that used in 'run_procflow'. Logging is now
a supported utility throughout the CLI, and can be used in any CLI class via
self.LOG.<log_level>(log_statement). Note that self.LOG.<log_level> does not have to
match the provided '--log-level' ran in the command. This flag is strictly just the
LOG level filter. I.e. if '--log-level info' was provided, levels
['info', 'debug', 'interactive'] would be shown. The lower the level, the more
logging channels will output.

::

     modified: geoips/commandline/commandline_interface.py
     modified: geoips/commandline/geoips_command.py

Enhancement
===========

Rewrite docs build in python
----------------------------

The docs build script has been re-written in Python. It now builds the docs in a temporary directory and only overwrites
the docs on disk if the build is successful. Please start calling docs/build_docs.py instead of docs/build_docs.sh.

::

     added: docs/build_docs.py
     added: docs/source/_templates/index.template.rst
     added: docs/source/_templates/sphinx_conf.template.py
     added: docs/source/releases/latest/Add-create_plugin_regitries-to-base_install.yaml
     modified: docs/build_docs.sh
     modified: pyproject.toml
     modified: pytest.ini
     modified: tests/integration_tests/base_install.sh
     deleted: tests/integration_tests/test_full_test.py

Enhancement
===========

Organize imports
----------------

imports were scattered across most readers. They are moved to the top, except optional dependency ones

::

     modified: geoips/plugins/modules/readers/abi_l2_netcdf.py
     modified: geoips/plugins/modules/readers/abi_netcdf.py
     modified: geoips/plugins/modules/readers/ahi_hsd.py
     modified: geoips/plugins/modules/readers/ami_netcdf.py
     modified: geoips/plugins/modules/readers/amsr2_netcdf.py
     modified: geoips/plugins/modules/readers/amsr2_remss_winds_netcdf.py
     modified: geoips/plugins/modules/readers/amsub_hdf.py
     modified: geoips/plugins/modules/readers/amsub_mirs.py
     modified: geoips/plugins/modules/readers/ascat_uhr_netcdf.py
     modified: geoips/plugins/modules/readers/atms_hdf5.py
     modified: geoips/plugins/modules/readers/ewsg_netcdf.py
     modified: geoips/plugins/modules/readers/geoips_netcdf.py
     modified: geoips/plugins/modules/readers/gmi_hdf5.py
     modified: geoips/plugins/modules/readers/imerg_hdf5.py
     modified: geoips/plugins/modules/readers/mimic_netcdf.py
     modified: geoips/plugins/modules/readers/modis_hdf4.py
     modified: geoips/plugins/modules/readers/saphir_hdf5.py
     modified: geoips/plugins/modules/readers/sar_winds_netcdf.py
     modified: geoips/plugins/modules/readers/scat_knmi_winds_netcdf.py
     modified: geoips/plugins/modules/readers/scat_noaa_winds_netcdf.py
     modified: geoips/plugins/modules/readers/seviri_hrit.py
     modified: geoips/plugins/modules/readers/sfc_winds_text.py
     modified: geoips/plugins/modules/readers/smap_remss_winds_netcdf.py
     modified: geoips/plugins/modules/readers/smos_winds_netcdf.py
     modified: geoips/plugins/modules/readers/ssmi_binary.py
     modified: geoips/plugins/modules/readers/ssmis_binary.py
     modified: geoips/plugins/modules/readers/viirs_netcdf.py
     modified: geoips/plugins/modules/readers/viirs_sdr_hdf5.py
     modified: geoips/plugins/modules/readers/wfabba_ascii.py
     modified: geoips/plugins/modules/readers/windsat_idr37_binary.py
     modified: geoips/plugins/modules/readers/windsat_remss_winds_netcdf.py

Enhancement
===========

NO TITLE
--------

``download_test_data.py`` now accepts dataset names and URLs, with added features
like optional rich text output. Progress towards integrating more functionality
into the GeoIPS CLI. Moved CIRA download URLs to a YAML file for easier management.

::

     added: setup/test-data-urls.yaml
     modified: setup/download_test_data.py

Enhancement
===========

Added new geoips list source-names command
------------------------------------------

*From GEOIPS#737: 2024-8-12, Discuss how to handle reader ``source_names`` attribute*

This branch creates a requested command from the 2024 GeoIPS Tutorial, called
'geoips list source-names'. This was created as source_names are a buried, but
essential feature of reader plugins, and this information isn't included in CLI
commands except when listing / describing product plugins. This also doesn't
guarantee that all source names are actually exposed via the CLI, only those which
are used within products. This new command searches throughout GeoIPS and
corresponding plugin packages for source_names implemented in reader plugins. We
added a new ``source_names`` attribute to core GeoIPS readers which we then add to
reader entries in plugin registries. This information can then be retrieved
using the CLI to easily expose source_names, and the readers which make use of those
source_names.

We now deprecate reader plugins which do not make use of the module-level
``source_names`` attribute. Reader plugins which don't have that attribute included
will be fully deprecated when GeoIPS v2.0.0 is released.

::

     modified: docs/source/userguide/command_line.rst
     modified: geoips/commandline/ancillary_info/alias_mapping.yaml
     modified: geoips/commandline/ancillary_info/cmd_instructions.yaml
     modified: geoips/commandline/geoips_list.py
     modified: geoips/create_plugin_registries.py
     modified: geoips/plugins/modules/readers/abi_l2_netcdf.py
     modified: geoips/plugins/modules/readers/abi_netcdf.py
     modified: geoips/plugins/modules/readers/ahi_hsd.py
     modified: geoips/plugins/modules/readers/ami_netcdf.py
     modified: geoips/plugins/modules/readers/amsr2_netcdf.py
     modified: geoips/plugins/modules/readers/amsr2_remss_winds_netcdf.py
     modified: geoips/plugins/modules/readers/amsub_hdf.py
     modified: geoips/plugins/modules/readers/amsub_mirs.py
     modified: geoips/plugins/modules/readers/ascat_uhr_netcdf.py
     modified: geoips/plugins/modules/readers/atms_hdf5.py
     modified: geoips/plugins/modules/readers/ewsg_netcdf.py
     modified: geoips/plugins/modules/readers/geoips_netcdf.py
     modified: geoips/plugins/modules/readers/gmi_hdf5.py
     modified: geoips/plugins/modules/readers/imerg_hdf5.py
     modified: geoips/plugins/modules/readers/mimic_netcdf.py
     modified: geoips/plugins/modules/readers/modis_hdf4.py
     modified: geoips/plugins/modules/readers/saphir_hdf5.py
     modified: geoips/plugins/modules/readers/sar_winds_netcdf.py
     modified: geoips/plugins/modules/readers/scat_knmi_winds_netcdf.py
     modified: geoips/plugins/modules/readers/scat_noaa_winds_netcdf.py
     modified: geoips/plugins/modules/readers/seviri_hrit.py
     modified: geoips/plugins/modules/readers/sfc_winds_text.py
     modified: geoips/plugins/modules/readers/smap_remss_winds_netcdf.py
     modified: geoips/plugins/modules/readers/smos_winds_netcdf.py
     modified: geoips/plugins/modules/readers/ssmi_binary.py
     modified: geoips/plugins/modules/readers/ssmis_binary.py
     modified: geoips/plugins/modules/readers/viirs_netcdf.py
     modified: geoips/plugins/modules/readers/viirs_sdr_hdf5.py
     modified: geoips/plugins/modules/readers/wfabba_ascii.py
     modified: geoips/plugins/modules/readers/windsat_idr37_binary.py
     modified: geoips/plugins/modules/readers/windsat_remss_winds_netcdf.py
     added: tests/unit_tests/commandline/test_geoips_list_source_names.py

Documentation
=============

Add additional info to ram system install requirements section
--------------------------------------------------------------

This existed elsewhere in the docs, but is more clear when included here in the install requirements.

::

     modified: docs/source/new-docs/getting-started/system-requirements/index.rst

Documentation
=============

Add numpy docstrings and examples to coding standards
-----------------------------------------------------

Throughout GeoIPS, we have inconsistent coding standards.
The numpy docstring format is an external standard we already use,
and so we want that to be explicit in our documentation.
This adds explicit info on using numpy docstrings, as well as examples.

::

     modified: docs/source/new-docs/contribute/coding_standards.rst

Documentation
=============

Write docstrings for base_paths
-------------------------------

Docstrings for base_paths were out of date. They have now been updated.

::

     modified: geoips/filenames/base_paths.py

Refactor
========

Ensure consistent module aliases
--------------------------------

refactor ensuring consistent module aliases

::

     modified: geoips/plugins/modules/readers/ascat_uhr_netcdf.py
     modified: geoips/plugins/modules/readers/gmi_hdf5.py
     modified: geoips/plugins/modules/readers/smos_winds_netcdf.py
     modified: geoips/plugins/modules/readers/ssmis_binary.py

Refactor
========

Refactor base_paths
-------------------

Base paths was originally very short, but has been added to over time. The original structure did not scale well. The
file original file very difficult to read, comprehend and/or maintain. File has been refactored.

::

     modified: geoips/filenames/base_paths.py
