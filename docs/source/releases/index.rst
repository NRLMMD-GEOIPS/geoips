.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _release_notes:

Release Notes
*************

Latest (version on cutting edge of git)
---------------------------------------

.. toctree::
   :maxdepth: 1

   latest

Version 1.14
------------

.. toctree::
   :maxdepth: 1

   v1_14_0a0

Version 1.13
------------

.. toctree::
   :maxdepth: 1

   v1_13_1
   v1_13_0
   v1_13_0a0

Version 1.12
------------

Added documentation and enhancements for coding standards, fixed bugs in polar data, log functions, and Dockerfile;
Introduced documentation for PEP8, linters, and plugin registries; Refactored optional imports, plugin registries. Fixed
issues with create_plugin_registries, ATMS platform names, and pytest dependencies.

.. toctree::
   :maxdepth: 1

   v1_12_4
   v1_12_3
   v1_12_2
   v1_12_2a0
   v1_12_1
   v1_12_0

Version 1.11
------------

Removed flake8_docstring_only flag from test_all.sh and full_test.sh across the repository. Fixed issues in integration
tests and ensured full flake8 tests applied.

.. toctree::
   :maxdepth: 1

   v1_11_7
   v1_11_7a0
   v1_11_6
   v1_11_5
   v1_11_5a0
   v1_11_3
   v1_11_3a0
   v1_11_2
   v1_11_1
   v1_11_1a0
   v1_11_0

Version 1.10
------------

Updated interface names throughout the code base, moved YAML sector files to new directories within the geoips/plugins
structure, added support for both the old and new dynamic sector YAML formatting, and renamed plugins to enhance
clarity. Introduced a try/except block in sector_utils/tc_tracks.py to support both old and new dynamic sector YAML
formats. Consolidated both dynamic and static sectors under the unified directory structure in
geoips/plugins/yaml/sectors, and renamed various modules to reflect their functionalities more accurately.

.. toctree::
   :maxdepth: 1

   v1_10_3
   v1_10_2
   v1_10_1
   v1_10_0
   v1_10_0a13
   v1_10_0a12
   v1_10_0a11
   v1_10_0a10
   v1_10_0a9
   v1_10_0a8
   v1_10_0a7
   v1_10_0a6
   v1_10_0a5
   v1_10_0a4
   v1_10_0a3
   v1_10_0a2
   v1_10_0a1
   v1_10_0a0

Version 1.9
-----------

Removed GEOIPS BASEDIR references and introduced GEOIPS_TESTDATA_DIR and GEOIPS_DEPENDENCIES_DIR in
filenames/base_paths.py, updated and implemented sphinx-apidoc for Sphinx documentation builds, finalized RST
documentation outline to align with SharePoint documentation, replaced setup.py with pyproject.toml for project setup,
added "cbar_tick_labels" and "cbar_spacing" fields in Rain colormap mpl_color_info, allowed processing when no tropical
cyclones are present in the database, installed geoips[doc, test, lint] dependencies in setup.sh, and configured code
style to ignore flake8 W503 due to conflicts with black.

.. toctree::
   :maxdepth: 1

   v1_9_2
   v1_9_1
   v1_9_0

Version 1.8
-----------

Renamed SSMI/S 89GHz products to 91GHz, updated F-16 SSMI/S scaling, resolved basename error, added geoips_clavrx to
test_full_install, and corrected minor sphinx build warnings. Fixed tests, ensured accurate product naming, and improved
installation and documentation processes.

.. toctree::
   :maxdepth: 1

   v1_8_1
   v1_8_0

Version 1.7
-----------

Updated matplotlib version dependency, extended SAR incident angle range, and converted CHANGELOG and documentation
formats to RST. Removed outdated sections, fixed minor documentation issues, and improved documentation organization and
building process.

.. toctree::
   :maxdepth: 1

   v1_7_0

Version 1.6
-----------

Added resource usage statistics, documentation updates, and code style enforcement checks. Fixed numpy builtin aliases,
product family typos, and output requirements.

.. toctree::
   :maxdepth: 1

   v1_6_3
   v1_6_1
   v1_6_0

Version 1.5
-----------

Updated the Python installation process, added alternate command line arguments functions, created unique storm
directory names for invests, and fixed bugs. Expanded test repository updates and improved metadata handling.

.. toctree::
   :maxdepth: 1

   v1_5_3
   v1_5_2
   v1_5_1
   v1_5_0

Version 1.4
-----------

Updated documentation and installation requirements, added new test scripts and functionality. Fixed real-time
processing and coverage checks.

.. toctree::
   :maxdepth: 1

   v1_4_8
   v1_4_7
   v1_4_6
   v1_4_5
   v1_4_4
   v1_4_3
   v1_4_2
   v1_4_1
   v1_4_0

Version 1.3
-----------

Replaced instances of 'atcf' with 'tc', removed support for GEOIPSFINAL and GEOIPSTEMP, and consolidated directories
into 'geoips_outdirs.' Added dev/title.py interface, updated template pull request ticket, allowed passing
'title_copyright,' and added new DATABASESUCCESS and DATABASEFAILURE string checks.

.. toctree::
   :maxdepth: 1

   v1_3_2
   v1_3_1
   v1_3_0

Version 1.2
-----------

Updated bdeck parser, SMOS text winds, test_interfaces.py, attribute names, call signatures; added ABI test scripts,
Software Requirements Specification. Replaced original_source_filename with original_source_filenames; simplified setup,
command line args checking, installation steps.

.. toctree::
   :maxdepth: 1

   v1_2_5
   v1_2_4
   v1_2_3
   v1_2_2
   v1_2_1
   v1_2_0

Version 1.1
-----------

Addition of new features like MODIS reader, stitched product output, sector overpass database, and Visible global
stitched. Refactoring for Python 3 operation, and resolving errors in MODIS processing and RGB MTIF color issue. There
are also breaking changes including modularized PMW algorithms, changed dictionary structures, and standardized platform
names.

.. toctree::
   :maxdepth: 1

   v1_1_17
   v1_1_16
   v1_1_15
   v1_1_14
   v1_1_13
