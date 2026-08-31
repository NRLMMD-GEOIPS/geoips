:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Scope of GeoIPS
===============

The GeoIPS "core" package covers data processing from **reading and reformatting** source
data into the common internal GeoIPS representation, through **algorithm and product
application**, to **writing** user-configurable output formats (imagery, NetCDF, GeoTIFF,
text, and more). This processing is orchestrated by :ref:`Order-Based Processing
<order-based-processing>`.

The following are intentionally **outside** the scope of the GeoIPS core and are treated as
site-specific implementations:

* Data collection and ingest scheduling.
* Data transfer between systems.
* Product dissemination and archival.
* Operational job scheduling (though GeoIPS can integrate with tools such as ``cylc``).

See :ref:`what is GeoIPS <getting-started>` for the high-level overview and
:ref:`order-based-processing` for the processing model.
