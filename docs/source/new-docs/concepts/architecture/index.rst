:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

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
