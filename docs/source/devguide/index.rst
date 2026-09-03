.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _devguide:

Developer Guide
===============

This guide covers the **internals** of GeoIPS 2.0 that plugin and core developers
need, but that most users do not. It is the counterpart to the task-oriented
:ref:`user documentation <getting-started>` and the :ref:`concepts <concepts>` and
:ref:`tutorials <tutorials>` sections.

If you are trying to *use* GeoIPS or *write a plugin*, start with the
:ref:`tutorials <tutorials>`. If you are working on the GeoIPS engine itself — the
Order-Based Processing (OBP) machinery, the DataTree data model, the class-based
plugin base classes, or the CI system — this is the right place.

.. note::

   This section is being expanded as part of the GeoIPS 2.0 documentation overhaul.
   Developer-facing pages migrated here from the historical ``docs/dev/`` directory,
   plus new internals references, will be linked below as they land.

.. toctree::
   :maxdepth: 1
   :caption: Internals

   converting-module-to-class
   datatree-spec

.. More developer-guide child pages are added to this toctree as they are created:
   OBP machinery internals, script datatree developer notes.
