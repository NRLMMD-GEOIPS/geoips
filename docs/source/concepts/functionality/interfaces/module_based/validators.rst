.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _validators_functionality:

********************
Validators in GeoIPS
********************

A validator is a module-based GeoIPS plugin designed to produce 'validation' metrics
between a produced dataset and a dataset from a known source of truth for a given use
case. These metrics could be as simple as an absolute difference product between the
output and truth dataset, or it could be more complex such as producing statistics
derived between those two datasets (say, comparing them to produce a data for a
histogram), would would be used by an `output formatter <create-output-formatter>`_.

An output formatter is a module-based GeoIPS plugin designed to output a dataset
to a file. This encompasses many varied types of output, including geotiff,
netCDF, and imagery. Output formatters vary in complexity depending on the
output type.

Every validator plugin at its core should expect these two variables:

1. xarray_obj (produced dataset)
2. truth_xarray_obj (source of truth dataset)

Additional arguments can be specified based on the family the validator falls under. The
actual validation performed by the plugin is up to the developer creating that plugin.

Output formatters can be executed in two ways:

1. **Specification at the Command Line:** Validators are specified
as arguments at the command line. For example:

   .. code-block:: bash

      --validator <validator name>

2. **Direct Invocation:** Call the validator from within a program:

   .. code-block:: python

      from xarray import Dataset

      from geoips.interfaces import validators

      validator_name = "difference"
      validator = validators.get_plugin(validator_name)

      # Replace 'Dataset()' with the actual produced and truth datasets
      ds = validator(xarray_obj=Dataset(), truth_xarray_obj=Dataset())
