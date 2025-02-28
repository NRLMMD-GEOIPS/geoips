.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _describe-readers:

Get to know the GeoIPS Readers
******************************

GeoIPS readers are module-based plugins that create a method of reading in many types of
satellite derived data. This doesn't mean you cannot create other types of data readers
too, such as .csv, .xls, etc. GeoIPS is primarly used as a package for Geo-informational
data, however if you purpose in a plugin that reads different types of data, the world
is your oyster.

GeoIPS readers return a dictionary of xarrays minimally containing the following
variables.

.. _minimum-contents:

+------------------------------------------+--------------------------------------------------------+-----------------+
| Common Names(s)                          | Required Name in Xarray                                | Data Format     |
+==========================================+========================================================+=================+
| Latitude, Longitude                      | latitude, longitude                                    | float/int       |
+------------------------------------------+--------------------------------------------------------+-----------------+
| Variables of Interest                    | <customizable> but should match names used by products |  float/int      |
+------------------------------------------+--------------------------------------------------------+-----------------+
| Time of Observation                      | time                                                   | datetime object |
+------------------------------------------+--------------------------------------------------------+-----------------+
| Metadata attr: Data Source               | source_name                                            | string          |
+------------------------------------------+--------------------------------------------------------+-----------------+
| Metadata attr: Time of First Observation | start_datetime                                         | datetime object |
+------------------------------------------+--------------------------------------------------------+-----------------+
| Metadata attr: Time of Final Observation | end_datetime                                           | datetime object |
+------------------------------------------+--------------------------------------------------------+-----------------+

The ``source_name`` set it your reader correlates to the ``source_names`` property in
your products plugin. As an example, ``my_clavrx_products.yaml`` data is read in by the
`clavrx_hdf4 reader
<https://github.com/NRLMMD-GEOIPS/geoips_clavrx/blob/main/geoips_clavrx/plugins/modules/readers/clavrx_hdf4.py>`_,
which sets it source name as ``clavrx``. See line 125 of that file for proof! In every
product of ``my_clavrx_products.yaml``, we set the source name as ``clavrx`` since that
is the reader we want to use to load in our data. See ``My-Cloud-Top-Height`` below for
an example of that.

.. code-block:: yaml

    spec:
      products:
        - name: My-Cloud-Top-Height
          source_names: [clavrx]
          docstring: |
            CLAVR-x Cloud Top Height
          product_defaults: Cloud-Height
          spec:
            variables: ["cld_height_acha", "latitude", "longitude"]

The variables defined in the product above directly correlate to the variables contained
in the Xarray after being processed by the reader. If you changed those variables name
in your product, it wouldn't work!

As with any GeoIPS plugin, a reader is required to define the top level attributes
``interface``, ``family``, and ``docstring``.

Please see documentation for
:ref:`additional info on GeoIPS required attributes<required-attributes>`,

Reader Structure Overview
-------------------------

A GeoIPS reader is module-based, and therefore must have a ``call`` function, as do all
other module-based plugins. Readers generallly also have one or several ``read functions``,
that exist outside of the call function. Optionally, a reader can also include ``utility
functions`` that perform some kind of operation on inputs. We will discuss each of each
of these in further detail now.

* The ``call`` function.
    * The call function is the main driver of a GeoIPS reader. It accepts the keyword
      arguments (kwargs) that contain the list of files to be read, and a handful of
      instructions that adust how the reader functions.

* Reader functions
    * Populate Xarrays with data from the files themselves. They technically are
      optional if you include all of this in the call function, but it is best practice
      to create them.

* Utility functions
    * Perform operations on the inputs, typically to convert them to a format
      understandable by GeoIPS. This could be using ``np.meshgrid(lats, lons)`` to
      create a 2D array of latitude and longitude, or whatever else you envision.

* Unit tests
    * Unit testing to help test conformity and validity of the reader and test data.
      For more details see :ref:`unit_tests`.

See below for an example of all three functions signatures in action.

.. code-block:: python

    def convert_epoch_to_datetime64(time_array, use_shape=None):  # Utility Function

    def read_atms_file(fname, xarray_atms):  # Read Function

    def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=None):  # Call Function, with
    important kwargs

There are a few keypoints of the call function that should be talked about. First off,
is the metadata required by GeoIPS that is associated with your data. Mainly, there are
three key-pieces to the metadata that *must be defined*: ``start_datetime``, ``end_datetime``,
and ``source_name``. As we discussed earlier, this is how your product can find the correct
reader at runtime to load in your data.

Another important piece of the reader is the ``metadata_only`` section. While it's not
required, it gives users the option to only load in the metadata if that's all they need.
This allows GeoIPS to not load in very large files multiple times.

See below for an example of both of those keypoints.

.. code-block:: python

    xarrays[data_type].attrs["start_datetime"] = start_date
    xarrays[data_type].attrs["end_datetime"] = end_date
    xarrays[data_type].attrs["source_name"] = "viirs"

    if metadata_only is True:
        LOG.info(
            "metadata_only is True, reading only first file for metadata information and returning"
        )
        return {"METADATA": xarrays[data_type]}

The last keypoint of a GeoIPS reader is the *read* function. Again, while not required,
it is best practice to separate your read function from the call function, for clarity
and ease of use in the future. See below for an example of invoking a read function.

.. code-block:: python

    xarray_objs = {}
    for fname in fnames:
        xarray_objs[basename(fname)] = read_xarray_netcdf(fname)  # The read function is invoked here

    xarray_objs["METADATA"] = list(xarray_objs.vallues())[0][[]]
    """Different approach to the above code section that reads data and then sets the metadata afterward"""

    return xarray_objs

A Typical Read Function
-----------------------

When creating a read function in a GeoIPS Reader, it is largely the dealers choice (ie.
yourself). The read function needs to open the file and read the contents (:ref:`Remember the
Minimum Contents Table<minimum-contents>`) into a dictionary of xarrays to be passed
along to GeoIPS. However, as with any piece of code, there are some challenges that you
should be aware of.

The first challenge are 1-Dimensional (1D) Variables. It's ok if your variables are 1D,
so long as *all of them* are 1D. You may need to do some array manipulatoin to get
everthing even! This is a common issue particularly with time arrays.

Another issue is time formatting. For example ``TAI93``, ``UTC``, ``binary string``,
``seconds since epoch``... there are a lot of ways time is reported in data formats.
Consult the users guide for your data to figure out how to convert time variables to the
required datetime object format.

The last challenge that should be noted is reading in the necessary ``channels`` for your
product. GeoIPS cannot intelligently read required channels unless you code your reader
to do just that. Remember that your ``call`` script is invoked with the ``chans``
parameter. Use that information to save you and your customer's time!

Example Read Function from GMI
------------------------------

Shown below is the read function for GMI HDF5 based data. As mentioned previously, time
can be a challenge for readers, and in this case, GMI stores each element of time
separately, as it only comes as a 1D variable. It needs to be converted to 2D to mesh
with the 2D latitude, longitude, and tb data.

.. code-block:: python

    def read_gmi_file(fname, xarray_gmi):
        """Read a single GMI file fname."""
        fileobj = h5py.File(fname, mode="r")
        import pandas as pd
        import xarray as xr
        import numpy

        # get the variables ( tbt/lon(nscan,npix), tb(nscan,npix,nChan),....., time(ns))

        lon = fileobj["S1"]["Longitude"][()]
        lat = fileobj["S1"]["Latitude"][()]
        tb = fileobj["S1"]["Tb"][()]
        tb_hi = fileobj["S2"]["Tb"][()]  # for 166 and 183-7 GHz

        # time info for each scan
        yy = fileobj["S1"]["ScanTime"]["Year"][()]
        mo = fileobj["S1"]["ScanTime"]["Month"][()]
        dd = fileobj["S1"]["ScanTime"]["DayOfMonth"][()]
        hh = fileobj["S1"]["ScanTime"]["Hour"][()]
        mm = fileobj["S1"]["ScanTime"]["Minute"][()]
        ss = fileobj["S1"]["ScanTime"]["Second"][()]

        # setup time in datetime64 format required by geoips

        nscan = lat.shape[0]
        npix = lat.shape[1]  # 221 pixels per scan
        time_scan = np.zeros((nscan, npix))

        for i in range(nscan):
            time_scan[i:] = "%04d%02d%02d%02d%02d%02d" % (
                yy[i],
                mo[i],
                dd[i],
                hh[i],
                mm[i],
                ss[i],
            )

        # assignment of TB at each channel
        V10 = tb[:, :, 0]
        H10 = tb[:, :, 1]
        V19 = tb[:, :, 2]
        H19 = tb[:, :, 3]
        V23 = tb[:, :, 4]
        V37 = tb[:, :, 5]
        H37 = tb[:, :, 6]
        V89 = tb[:, :, 7]
        H89 = tb[:, :, 8]

        V166 = tb_hi[:, :, 0]
        H166 = tb_hi[:, :, 1]
        V183_3 = tb_hi[:, :, 2]
        V183_7 = tb_hi[:, :, 3]

        # close the h5 object
        fileobj.close()

        #          ------  setup xarray variables   ------

        # namelist_gmi  = ['latitude', 'longitude', 'V10', 'H10', 'V19','H19','V23', 'V37', 'H37', 'V89' ,'H89',
        #                   'V166', 'H166', 'V183-3','V183-7', 'time']

        final_xarray = xr.Dataset()
        if "latitude" not in xarray_gmi.variables.keys():
            # setup GMI xarray
            final_xarray["latitude"] = xr.DataArray(lat)
            final_xarray["longitude"] = xr.DataArray(lon)
            final_xarray["V10"] = xr.DataArray(V10)
            final_xarray["H10"] = xr.DataArray(H10)
            final_xarray["V19"] = xr.DataArray(V19)
            final_xarray["H19"] = xr.DataArray(H19)
            final_xarray["V23"] = xr.DataArray(V23)
            final_xarray["V37"] = xr.DataArray(V37)
            final_xarray["H37"] = xr.DataArray(H37)
            final_xarray["V89"] = xr.DataArray(V89)
            final_xarray["H89"] = xr.DataArray(H89)
            final_xarray["V166"] = xr.DataArray(V166)
            final_xarray["H166"] = xr.DataArray(H166)
            final_xarray["V183-3"] = xr.DataArray(V183_3)
            final_xarray["V183-7"] = xr.DataArray(V183_7)
            final_xarray["time"] = xr.DataArray(
                pd.DataFrame(time_scan)
                .astype(int)
                .apply(pd.to_datetime, format="%Y%m%d%H%M%S")
            )
        else:
            final_xarray["latitude"] = xr.DataArray(
                numpy.vstack([xarray_gmi["latitude"].to_masked_array(), lat])
            )
            final_xarray["longitude"] = xr.DataArray(
                numpy.vstack([xarray_gmi["longitude"].to_masked_array(), lon])
            )
            final_xarray["V10"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V10"].to_masked_array(), V10])
            )
            final_xarray["H10"] = xr.DataArray(
                numpy.vstack([xarray_gmi["H10"].to_masked_array(), H10])
            )
            final_xarray["V19"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V19"].to_masked_array(), V19])
            )
            final_xarray["H19"] = xr.DataArray(
                numpy.vstack([xarray_gmi["H19"].to_masked_array(), H19])
            )
            final_xarray["V23"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V23"].to_masked_array(), V23])
            )
            final_xarray["V37"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V37"].to_masked_array(), V37])
            )
            final_xarray["H37"] = xr.DataArray(
                numpy.vstack([xarray_gmi["H37"].to_masked_array(), H37])
            )
            final_xarray["V89"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V89"].to_masked_array(), V89])
            )
            final_xarray["H89"] = xr.DataArray(
                numpy.vstack([xarray_gmi["H89"].to_masked_array(), H89])
            )
            final_xarray["V166"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V166"].to_masked_array(), V166])
            )
            final_xarray["H166"] = xr.DataArray(
                numpy.vstack([xarray_gmi["H166"].to_masked_array(), H166])
            )
            final_xarray["V183-3"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V183-3"].to_masked_array(), V183_3])
            )
            final_xarray["V183-7"] = xr.DataArray(
                numpy.vstack([xarray_gmi["V183-7"].to_masked_array(), V183_7])
            )
            new_time = xr.DataArray(
                pd.DataFrame(time_scan)
                .astype(int)
                .apply(pd.to_datetime, format="%Y%m%d%H%M%S")
            )
            final_xarray["time"] = xr.DataArray(
                numpy.vstack(
                    [
                        xarray_gmi["time"].to_masked_array(),
                        new_time.to_masked_array(),
                    ]
                )
            )
        return final_xarray
