.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _scripting-tutorial:

Scripting with GeoIPS
*********************

This tutorial walks through driving GeoIPS from a Python script using the
:mod:`geoips.scripting` DataTree API — the same data model :ref:`Order-Based Processing
<order-based-processing>` uses. For the full API reference, see the
:ref:`scripting guide <scripting-guide>`.

We will build a small, self-contained script that computes cloud depth from synthetic
data, so it runs without any external data files.

The complete script
-------------------

.. literalinclude:: extending-with-plugins/examples/script_cloud_depth.py
   :language: python
   :lines: 4-

Step by step
------------

#. **Initialize a script tree.** Every scripting session starts by initializing a tree
   with :func:`~geoips.scripting.initialize_script_tree`, choosing a
   :ref:`retention policy <retention-policies>`:

   .. code-block:: python

       tree = initialize_script_tree(
           name="cloud_depth_demo",
           retention_policy=RetentionPolicy.keep_all,
       )

#. **Bring your own data.** Here we construct a synthetic ``xarray.Dataset`` with the
   coordinates and metadata GeoIPS expects and insert it with
   :func:`~geoips.scripting.add_data_step`. In a real script you would usually get this
   data from a GeoIPS reader instead (see the :ref:`scripting guide <scripting-guide>`).

#. **Manipulate data between steps.** :func:`~geoips.scripting.get_current_data` returns a
   mutable copy of the most recent data step. Edit it and reinsert it as a new step:

   .. code-block:: python

       current = get_current_data(tree)
       current["cloud_depth"] = (
           current["cloud_top_height"] - current["cloud_base_height"]
       ) * 0.001
       tree = add_data_step(tree, current, step_id="compute_cloud_depth")

#. **Read the result back out** with another :func:`~geoips.scripting.get_current_data`
   call.

Running it
----------

.. code-block:: bash

    python script_cloud_depth.py
    # [[4. 6.]]

.. note::

   This script is a real, tested example. It lives at
   ``docs/source/tutorials/extending-with-plugins/examples/script_cloud_depth.py`` and is
   executed by ``tests/unit_tests/docs/test_tutorial_examples.py``, so this tutorial's
   code stays runnable.

Next steps
----------

- Call real GeoIPS plugins (readers, algorithms, colormappers, output formatters) from a
  script — see the :ref:`scripting guide <scripting-guide>`.
- Capture a stable script as a reusable :ref:`OBP workflow <order-based-processing>`.
