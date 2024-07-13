:orphan:

.. dropdown:: Distribution Statement

 | # # # Distribution Statement A. Approved for public release. Distribution is unlimited.
 | # # #
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # #
 | # # # This program is free software: you can redistribute it and/or modify it under
 | # # # the terms of the NRLMMD License included with this program. This program is
 | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
 | # # # for more details. If you did not receive the license, for more information see:
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

Architecture
============

Assigned to: Jeremy
Due for review: June 10th

Done looks like:
 - Work done on a feature branch, eg. documentation-architecture-overview
 - Readable and followable, please use a grammar checker + spell checker
 - Passes doc8 checks, see the `sphinx RST Primer
   <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#restructuredtext-primer>`_`
   and checkout this tool I wrote for auto-formatting RST files:
   `pink <https://github.com/biosafetylvl5/pinkrst/tree/main>`_

   - Does NOT include

     - Any guidance on specific functionality
     - Any guidance on specific plugin/interfaces
     - Any guidance on specific ... anything
     - Detailed description of what an interface is - an overview is fine
     - Descriptions of specific code
     - Descriptions of what GeoIPS is
     - Coding guides

   - Does include

     - A description of the overall structure of GeoIPS
     - Descriptions of code paradigms
     - Rational on why GeoIPS is constructed like it is
     - An answer to the question: what are the "building blocks of GeoIPS"
     - Understanding `oriented information <https://docs.divio.com/documentation-system/explanation/>`_

 - A PR from your feature branch to ``main`` 😊
