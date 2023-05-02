Pre Version 1.10.0a12 (2023-05-02)
**********************************

* Add sector_adjusters interface, and use from single_source procflow

Major New Functionality
=======================

Add sector_adjusters interface
------------------------------

This is only used within the recenter_tc repository, but interface added here.

::

  new: geoips/interfaces/module_based/sector_adjusters.py
  modified: geoips/interfaces/__init__.py

Update single_source procflow to use new sector_adjusters interface
-------------------------------------------------------------------

Was previously using "find_entry_point" directly.

::

  modified:   plugins/modules/procflows/single_source.py
