.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _deployguide:

Deploying and Operating GeoIPS
==============================

This guide covers running GeoIPS beyond a single interactive command — in batch, in
near-real-time, and in operational deployments. It builds on the
:ref:`installation instructions <installation>` and the
:ref:`Order-Based Processing <order-based-processing>` model.

.. note::

   GeoIPS "core" handles processing (read → transform → compute → visualize → output).
   Data collection, transfer, dissemination, and job scheduling are site-specific and are
   intentionally :ref:`outside the core scope <geoips_scope>`. This guide describes how to
   drive GeoIPS from those systems.

.. contents::
   :local:

Configuring GeoIPS for a deployment
-----------------------------------

Operational deployments should pin configuration explicitly rather than relying on
defaults. GeoIPS resolves settings with the priority **environment variables > project
``.geoips.yaml`` > built-in defaults** (see :ref:`geoips-config`). The settings that most
often need to be set for a deployment are:

* ``GEOIPS_OUTDIRS`` — the root for all written output.
* ``GEOIPS_PACKAGES_DIR`` — where your plugin packages live.
* ``GEOIPS_TESTDATA_DIR`` — test data location (for verification runs).
* Output sub-paths (imagery, NetCDF, GeoTIFF, logs) under ``geoips.output_paths.*``.
* ``geoips.logging.level`` / ``GEOIPS_LOGGING_LEVEL`` — logging verbosity.

A checked-in ``.geoips.yaml`` at the project root keeps a deployment reproducible while
still allowing per-host overrides via environment variables.

Building plugin registries
--------------------------

GeoIPS discovers plugins through a **registry** built from the installed plugin packages.
Rebuild the registries after installing GeoIPS, installing or updating a plugin package, or
adding new plugins:

.. code-block:: bash

    geoips config create-registries

In an operational pipeline, run this as part of your deployment/update step (not on every
processing invocation). Confirm the plugins you expect are present with ``geoips list``:

.. code-block:: bash

    geoips list interfaces -i
    geoips list workflows
    geoips list products -p <your_package>

Running products in batch
-------------------------

The unit of operational processing is an :ref:`OBP workflow <order-based-processing>`. Run
a registered workflow over a set of input files:

.. code-block:: bash

    geoips run order_based <workflow_name> <input_files...>

To process many cases, drive ``geoips run order_based`` from a shell loop, a scheduler, or
a Python driver — one invocation per workflow/data group. Per-run parameters (sector,
output type, thresholds) can be supplied as :ref:`overrides <running-obp>` without editing
the workflow:

.. code-block:: bash

    for datadir in /data/incoming/*/ ; do
        geoips run order_based abi_static_infrared_imagery_clean "$datadir"/* \
            -g logging_level=info
    done

For reproducible, comparison-checked runs (regression testing a deployment), use a
workflow's ``test`` section via ``geoips test workflow <name>``.

Near-real-time (NRT) processing
-------------------------------

Near-real-time processing watches for newly arrived data and runs a workflow as soon as it
appears. The general pattern is:

1. A file-arrival trigger (an inotify watch, a message queue, or a polling loop).
2. A GeoIPS invocation (``geoips run order_based ...``) or a Python
   :ref:`script <scripting-guide>` for the new data.
3. Output written under ``GEOIPS_OUTDIRS`` and (optionally) disseminated by your site
   tooling.

A concrete, self-contained example using ``inotifywait`` is provided in the
:ref:`near-real-time processing tutorial <using-inotifywait>`. For more complex NRT logic
(compositing, conditional products, custom retention), drive GeoIPS plugins directly with
the :ref:`scripting API <scripting-guide>`.

Managing memory and performance
-------------------------------

Large operational runs are usually bound by memory and I/O. GeoIPS provides several levers:

* **Retention policies** (when :ref:`scripting <retention-policies>`) control how much
  intermediate data is kept in the processing tree — use ``metadata_only`` or
  ``current_only`` for memory-sensitive processing.
* **Sectored and resampled reads** — many readers accept ``sectored_read`` /
  ``resampled_read`` arguments so only the needed region is read and reprojected, reducing
  memory for full-disk geostationary data.
* **Geolocation caching** — geostationary geolocation is cached
  (``geoips.cache.geolocation_cache_backend``); point the cache at fast storage.

Integrations
------------

* **Product databases** — the :ref:`databases interface <databases_functionality>` lets a
  deployment record produced outputs (and query prior products, e.g. for compositing) via a
  database plugin, without hard-coding a particular backend.
* **External schedulers** — GeoIPS invocations are ordinary commands and integrate with
  workflow managers such as ``cylc`` or with ``cron`` for time-based triggers.

See also
--------

* :ref:`geoips-config` — the full configuration reference.
* :ref:`running-obp` — running workflows and applying overrides.
* :ref:`command_line` — the complete CLI reference.
* :ref:`using-inotifywait` — a worked near-real-time example.
