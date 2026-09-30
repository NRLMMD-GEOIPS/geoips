.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _procflows_functionality:

Processing Workflows (Procflows) in GeoIPS
******************************************

A processing workflow (procflow) is a class-based GeoIPS plugin that
determines the "steps" that are used for a particular type of processing.
Essentially, the procflow is the driver of GeoIPS processing that determines
the order in which to call other plugins, such as algorithms and output formatters.
Although it is possible to create one's own processing workflow, the built-in
procflows are designed to cover nearly any use-case, and upcoming development
will increase the number of cases that are covered. It is extremely unlikely
that a user will need to develop their own procflow.

Examples of procflow plugins can be found in the list of GeoIPS built-in
`procflows <https://github.com/NRLMMD-GEOIPS/geoips/tree/main/geoips/plugins/modules/procflows>`__.
Most cases involving the production of basic imagery will use the
``single_source`` procflow. More complex cases may not be able to use ``single_source``,
but can often be handled by the
``config_based`` or
`data_fusion <https://github.com/NRLMMD-GEOIPS/data_fusion>`_
procflows.

Procflows can be executed in two ways:

1. **Specification at the Command Line:** Procflows are specified
as the primary argument at the command line when running GeoIPS. The recommended procflow
in GeoIPS 2.0 is the :ref:`Order-Based Procflow <order-based-processing>`, called as follows:

   .. code-block:: bash

      geoips run order_based <workflow> <files>

The legacy ``single_source``, ``config_based``, and ``data_fusion`` procflows are still
available (``geoips run single_source`` ...) but are deprecated; OBP can produce everything
they can. See :ref:`running-obp` to run a workflow.

2. **Direct Invocation:** Procflows can be called within another program:

   .. code-block:: python

      from geoips.interfaces import procflows
      procflow_name = "single_source"
      procflow = procflows.get_plugin(procflow_name)

Note, however, that since procflows are the "drivers" of GeoIPS processing, it is
advised to use the GeoIPS command line interface to run them in most situations.
