Pre Version 1.10.0a12 (2023-05-01)
**********************************

* Remove sectorfiles option from commandline
* Add new sector interface

Major New Functionality
=======================

Add new sector interface
------------------------

This interface can be used for both dynamic templates and fully specified
static yaml-based sectors.

::

  new file: interfaces/yaml_based/sectors.py

Breaking Changes
================

Remove sectorfiles option from commandline
------------------------------------------

Sectors are now fully fledged plugins, so we can just pass the list of
sectors command line, we do not have to pass the full path to the associated
file.  Remove all references to "sectorfiles" arguments, and rely on the
sector list.

::

  modified: geoips/commandline/args.py
  modified: geoips/plugins/modules/procflows/single_source.py
  modified: geoips/sector_utils/utils.py
  modified: tests/scripts/abi.static.Infrared.imagery_annotated.sh
  modified: tests/scripts/abi.static.Visible.imagery_annotated.sh
  modified: tests/scripts/documentation_imagery.sh
  modified: tests/scripts/ewsg.static.Infrared.imagery_clean.sh
  modified: tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh
