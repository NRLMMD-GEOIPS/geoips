# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.


"""Generic Satpy reader.

Provides a GeoIPS wrapper for basic Satpy reader functionality. For more detailed
documentation of Satpy, see the documentation here:
https://satpy.readthedocs.io/en/stable/. This reader creates a Scene object with
the provided filenames and specified reader, then loads provided channels. The
satpy_reader, and fnames arguments are passed to the Scene constructor.  The
Scene object is then reorganized into a Dictionary of XArray Dataset objects as
required by the GeoIPS reader interface.  The various additional arguments to
the Scene constructor and its load method are provided as optional arguments to
the call function in this plugin.  This allows any arguments required by a
particular Satpy reader to be passed via the GeoIPS command line interface
reader_kwargs argument. The reader_kwargs argument should provide a string
containing a JSON Object mapping call arguments with their desired values.

In order to map the structure of a Satpy Scene to the Dictionary of Datasets, an
additional argument named "channel_groups" should be provided via reader_kwargs.
The argument is a dictionary that groups desired channels by resolution.  This
dictionary's keys should be strings representing the name of each group and the
values should be a list of channel names that have the same resolution. The name
of each group will be used as the keys of the output dictionary and the list of
channels will be grouped together as a Dataset stored as the associated value to
the key.  So for example the following channel_groups JSON Object could be used
to read a selection of visible and IR GOES16 data:
"channel_groups":{"0.5km":["C02"], "2km":["C13", "C14"]}

While Satpy provides a very large number of readers, a very small number of them
have been used with this plugin.  This plugin should be considered experimental
and is not guaranteed to work with all of Satpy's readers.
"""

import glob
import logging
from typing import Any, Dict, List, Optional, Tuple

import dask
import dask.array
import pyresample.geometry
import satpy
import xarray as xr

log = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "generic_satpy"


DEFAULT_COORD_CHUNK = 4096


def call(
    fnames: List[str],
    source_name: str,
    satpy_reader: str,
    channel_groups: Dict[str, List[str]],
    platform_name: Optional[str] = None,
    platform_name_attr: str = "platform_name",
    metadata_only: bool = False,
    chans: Optional[List[str]] = None,
    area_def: Optional[pyresample.geometry.AreaDefinition] = None,
    self_register: bool = False,
    roi: float = 3000,
    satpy_reader_kwargs: Optional[Dict[str, Any]] = None,
    load_kwargs: Optional[Dict[str, Any]] = None,
    force_compute: bool = True,
    coord_chunks: int = DEFAULT_COORD_CHUNK,
) -> Dict[str, xr.DataArray]:
    """Generic Satpy Reader.

    Parameters
    ----------
        fnames : List[str]
            * List of strings, full paths to files
        source_name : str
            * The GeoIPS plugin source name.
        satpy_reader : str
            * The name of the Satpy reader to use. See
              https://satpy.readthedocs.io/en/stable/reading.html for a full
              list of readers.
        channel_groups : Dict[str, List[str]]
            * A dictionary that groups desired channels by resolution.  The
              read Satpy Scene will be unpacked into the structure described by
              this dictionary. The keys should be strings representing the name
              of each group and the values should be a list of channel names
              that have the same resolution. The name of each group will be used
              as the keys of the output dictionary and the list of channels will
              be grouped together as a Dataset stored as the associated value to
              the key.  So for example the following channel_groups dictionary
              could be used to read a selection of visible and IR GOES16 data:
              `{"0.5km":["C02"], "2km":["C13", "C14"]}`
        platform_name : str, default=None
            * The GeoIPS plugin platform name. If set to `None`, then the
              platform name will be looked up from the attributes of the first
              encountered channel. The `platform_name_attr` can be used to
              control which attribute the platform name will be looked up from.
        platform_name_attr : str, default="platform_name"
            * The attribute used to look up the platform name if no platform
              name is provided.  The attributes dictionary of the first channel
              encountered by the code will be used to look up the platform name.
              This assumes that the attribute is not nested within a
              sub-dictionary of the attributes dictionary.
        metadata_only : bool, default=False:
            * Return before actually reading data if True
        chans : List[str], default=None
            * Required by the GeoIPS interface, but is ignored by the reader.
        area_def : pyresample.AreaDefinition, default=None
            * Required by the GeoIPS interface, but is ignored by the reader.
        self_register : str or bool, default=False
            * Required by the GeoIPS interface, but is ignored by the reader.
        roi : float, default=3000.0
            * Radius of influence used by GeoIPS interpolator.
        satpy_reader_kwargs : Dict[str, Any], default=None
            * If provided, these kwargs will be passed to the `reader_kwargs`
              argument of the Satpy `Scene` constructor.
        load_kwargs : Dict[str, Any], default=None
            * If provided, these kwargs will be passed to the `load` method of
              the generated Satpy `Scene` object.
        force_compute : bool, default=True
            * When Satpy loads data, it provides `DataArray` objects populated
              by Dask arrays.  By default, this reader will force these to be
              computed prior to providing `Dataset`s downstream.  However, if
              downstream code can handle receiving Dask arrays, then this flag
              can be set to `False` to prevent the conversion.
        coord_chunks : int, default=4096
            * In order to ensure consistency when reading coordinate data from
              a loaded `Scene`, the data will be read as a Dask array an then
              converted to a Numpy array.  This argument controls the chunk size
              used by Dask during this opration.

    dict of xarray.Datasets
        * dictionary of xarray.Dataset objects with required Variables and
          Attributes.
        * Dictionary keys can be any descriptive dataset ids.
        * The `channel_groups` argument controls how to map the read Satpy
          `Scene` object to this dictionary.
    """
    scene = satpy.Scene(
        filenames=fnames,
        reader=satpy_reader,
        reader_kwargs=satpy_reader_kwargs,
    )

    all_channels = []
    for channel_names in channel_groups.values():
        all_channels.extend(channel_names)

    if load_kwargs is None:
        load_kwargs = {}

    scene.load(
        all_channels,
        **load_kwargs,
    )

    output_datasets = {}
    for group_name, channel_names in channel_groups.items():
        lons, lats = (None, None)
        is_first_channel = True
        data_dict = {}
        for channel_name in channel_names:
            channel = scene[channel_name]
            if is_first_channel:
                is_first_channel = False
                lons, lats = _compute_coords(channel, coord_chunks)

                if platform_name is None:
                    platform_name = channel.attrs[platform_name_attr]

            if force_compute and not metadata_only:
                channel = channel.compute()

            data_dict[channel_name] = channel

        data_dict["longitude"] = lons
        data_dict["latitude"] = lats

        group_dataset = xr.merge([data_dict], compat="override")
        group_dataset.attrs["source_name"] = source_name
        group_dataset.attrs["platform_name"] = platform_name
        group_dataset.attrs["data_provider"] = "satpy"
        group_dataset.attrs["start_datetime"] = scene.start_time
        group_dataset.attrs["end_datetime"] = scene.end_time
        group_dataset.attrs["interpolation_radius_of_influence"] = roi

        output_datasets[group_name] = group_dataset
        output_datasets["METADATA"] = group_dataset[[]]

    return output_datasets


def _compute_coords(
    channel: xr.DataArray, coord_chunks: int
) -> Tuple[xr.DataArray, xr.DataArray]:
    lons_dask, lats_dask = channel.attrs["area"].get_lonlats(chunks=coord_chunks)
    lons_np, lats_np = dask.array.compute(lons_dask, lats_dask)

    coord_x = channel.coords["x"]
    coord_y = channel.coords["y"]
    lons = xr.DataArray(lons_np, dims={"y": coord_y, "x": coord_x})
    lats = xr.DataArray(lats_np, dims={"y": coord_y, "x": coord_x})

    return lons, lats


def get_test_files(test_data_dir):
    """Generate testing xarray from test data."""
    filepath = test_data_dir + "/test_data_noaa_aws/data/goes16/20200918/1950/*.nc"
    filelist = glob.glob(filepath)
    channel_groups = {"0.5km": ["C02"], "2km": ["C11", "C12", "C13"]}
    tmp_xr = call(filelist, "abi", "abi_l1b", channel_groups, "goes16")
    if len(filelist) == 0:
        raise NameError("No files found")
    return tmp_xr


def get_test_parameters():
    """Generate test data key for unit testing."""
    return [
        {"data_key": "0.5km", "data_var": "C02", "mean": 13.058826},
        {"data_key": "2km", "data_var": "C11", "mean": 276.52844},
        {"data_key": "2km", "data_var": "C12", "mean": 256.0734},
        {"data_key": "2km", "data_var": "C13", "mean": 279.05426},
    ]
