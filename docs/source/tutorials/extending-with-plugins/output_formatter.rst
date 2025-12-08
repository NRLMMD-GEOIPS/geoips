.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _create-output-formatter:

Extend GeoIPS with a New Output Formatter
*****************************************

GeoIPS Output Formatters define a method for plotting imagery or outputting data to a
specific file format. Output formatters take in Xarray data, or a dictionary of Xarray
data, and convert it into something interpretable.

This includes:
  * A NetCDF file
  * An image
  * A HDF5 file
  * And many other formats

Every output formatter plugin, and every other GeoIPS plugin, is required to have the
top level attributes
``interface``, ``family``, and ``docstring``.

Please see documentation for
:ref:`additional info on these GeoIPS required attributes<required-attributes>`

You can read more about them, including their required arguments and keyword arguments
(kwargs) `here
<https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/interfaces/module_based/output_formatters.py>`_.
The arguments you supply your output formatter completely depend on the intent of your
output. For example, if outputting an image, the arguments provided to the required
Module-based ``call`` function, will be very different than that of a NetCDF output.

For example, this is the call signature of the ``netcdf_geoips`` output formatter, which
is under the ``xarray_data`` family.

.. code-block:: python

  interface = "output_formatters"
  family = "xarary_data"
  name = "netcdf_geoips"

  def call(xarray_obj, product_names, output_fnames):

Whereas the ``imagery_annotated`` output formatter call signtature, under the family
``imagery_overlay``, looks like this:

.. code-block:: python

  interface = "output_formatters"
  family = "imagery_overlay"
  name = "iamgery_annotated"

  def call(
    area_def,
    xarray_obj,
    product_name,
    output_fnames,
    clean_fname=None,
    product_name_title=None,
    mpl_colors_info=None,
    feature_annotator=None,
    gridline_annotator=None,
    product_datatype_title=None,
    bg_data=None,
    bg_mpl_colors_info=None,
    bg_xarray=None,
    bg_product_name_title=None,
    bg_datatype_title=None,
    remove_duplicate_minrange=None,
    title_copyright=None,
    title_formatter=None,
    output_dict=None,
  ):

We now see that the call signature of output formatters greatly depends on the intent of
the output data type. Now that we understand that, we can begin creating our own output
formatter.

Creating Your Own Output Formatter
----------------------------------

To start off, let's create a directory for our output formatter plugins.
::

  mkdir $MY_PKG_DIR/$MY_PKG_NAME/plugins/modules/output_formatters/
  cd $MY_PKG_DIR/$MY_PKG_NAME/plugins/modules/output_formatters/
  touch __init__.py

Once you've activated ``__init__.py``, we can move forward with creating our own output
formatter. Let's create a file called ``my_netcdf_output.py``, which will output our
CLAVR-x data in a specific netcdf format. Copy and paste the code below into that file.

.. code-block:: python

  """My NetCDF output format."""
  import logging

  LOG = logging.getLogger(__name__)

  interface = "output_formatters"
  family = "xarray_data"
  name = "my_netcdf_output"

  def call(xarray_obj, product_names, output_fnames):
      """Write GeoIPS style NetCDF to disk."""
      import xarray

      prod_xarray = xarray.Dataset()

      from geoips.geoips_utils import copy_standard_metadata

      copy_standard_metadata(xarray_obj, prod_xarray)
      for product_name in product_names:
          prod_xarray[product_name] = xarray_obj[product_name]

      prod_xarray = prod_xarray.assign_attrs(Starring="Richard Karn",
                                             Featuring="Johnathan Taylor Thomas",
                                             ProducedBy="Carmen Finestra")

      from geoips.plugins.modules.output_formatters.netcdf_xarray import (
          write_xarray_netcdf,
      )

      for ncdf_fname in output_fnames:
          write_xarray_netcdf(prod_xarray, ncdf_fname)
      return output_fnames

The file above is very simlar to GeoIPS `netcdf_geoips output formatter
<https://github.com/NRLMMD-GEOIPS/geoips/blob/main/geoips/plugins/modules/output_formatters/netcdf_geoips.py>`_,
however, in this case we add additional attributes to our xarray. When creating your own
output formatter, feel free to add attributes specific to your own needs.

Adding Your Output Formatter to pyproject.toml
----------------------------------------------

As with any other module-based plugin, we need to add it to our packages ``pyproject.toml``
so that GeoIPS can recognize it in its namespace and use it when called. To do so, change
directories to the top level of your package, and edit ``pyproject.toml`` to include the
lines shown below. Note: if you named your package something other than ``cool_plugins``,
replace that with your package name.
::

  [project.entry-points."geoips.output_formatters"]
  my_netcdf_output = "cool_plugins.plugins.modules.output_formatters.my_netcdf_output"

Once complete, you'll have to reinstall your package to so that GeoIPS recognizes the new
state of your package. This is required anytime you edit ``pyproject.toml``. Run the
command below to do just that.
::

  pip install -e $MY_PKG_DIR

Creating a Script that Uses our Output Formatter
------------------------------------------------

Note: this section assumes you have already completed the
:ref:`Products Section<create-a-product>`. As with many other types of plugins, they are
only a component of a Product. An output formatter is useless without a product that
makes use of it.

Now that GeoIPS recognizes your new output formatter, we should create a script that
uses it. Change directories to your tests/scripts directory, and create a new script
called ``clavrx.conus_netcdf.my-cloud-top-height-my-netcdf.sh``. Once you've done that,
copy and paste the code below into that file.

.. code-block:: bash

  geoips run single_source \
      $GEOIPS_TESTDATA_DIR/test_data_clavrx/data/goes16_2023101_1600/clavrx_OR_ABI-L1b-RadF-M6C01_G16_s20231011600207.level2.hdf \
      --reader_name clavrx_hdf4 \
      --product_name My-Cloud-Top-Height \
      --output_formatter my_netcdf_output \
      --filename_formatter geoips_netcdf_fname \
      --minimum_coverage 0 \
      --sector_list conus
  ss_retval=$?

Once you've added that to your file, you're ready to run your script. To do so, run the
command shown below.
::

  $MY_PKG_DIR/tests/scripts/clavrx.conus_netcdf.my-cloud-top-height-my-netcdf.sh

Look throught the log output for these lines. If you see them, you've successfully
created a new output formatter!
::

  :Starring = "Richard Karn" ;
  :Featuring = "Jonathan Taylor Thomas" ;
  :ProducedBy = "Carmen Finestra" ;
