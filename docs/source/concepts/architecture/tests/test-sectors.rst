Test Sectors for GeoIPS
=======================

We use small, pre-determined test sectors for testing. 
These sectors provide a variety of scene components 
including coast and land, edge of geostationary disk, day/night/terminator features etc. 

Naming Convention
-----------------

Test sector plugin names follow this format:

.. code-block::

   test_<satellite>_<proj>_<res>_<edge|nadir>_<day|night|terminator>_<OPTIONAL:tc|ar|volc>_<YYYYMMDDTHHMMZ>.yaml

Example
~~~~~~~

.. code-block::

   test_goes16_eqc_3km_edge_day_tc_20200918T1950Z

Components
~~~~~~~~~~

* **satellite**: The satellite platform (e.g., goes16, himawari8)
* **proj**: Projection type (e.g., eqc for Equidistant Cylindrical (Plate Carrée) projection)
* **res**: Resolution (e.g., 3km)
* **edge|nadir**: Satellite view position
* **day|night|term**: Illumination condition
* **tc|ar|volc**: Optional field for special event types:
  * tc: Tropical Cyclone
  * ar: Atmospheric River
  * volc: Volcano
* **YYYYMMDDTHHMMZ**: Timestamp in ISO format

Implementation Notes
--------------------

* All test sectors are 300x300 pixels in size
* Parsing sector names is not good practice.
* If metadata from plugin names needs to be tracked or used, explicit metadata will be added to the plugins themselves
  for sorting/searching
* Custom sorting of plugins can be implemented within the CLI based on plugin metadata
* The current plugin name format was chosen to provide reasonable default sorting order

File Naming Requirements
------------------------

* Filenames for individual test sector plugins do NOT have to match the plugin names (to avoid excessively long
  filenames on disk)
* For now, the following fields must be manually updated to match exactly:
  * ``area_id`` and ``name`` must match the plugin name
  * ``description`` and ``docstring`` must match each other

.. note::
   Eventually, plugins will be set up to automatically populate ``area_id`` and ``description`` if they are not set, but
   for now these must be manually maintained. The ``name`` and ``docstring`` fields are always required.
