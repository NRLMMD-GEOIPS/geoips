# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface module."""

from xarray import open_dataset

from geoips.interfaces.base import BaseModuleInterface


class ReadersInterface(BaseModuleInterface):
    """Interface for ingesting a specific data type.

    Provides specification for ingensting a specific data type, and storing in
    the GeoIPS xarray-based internal format.
    """

    name = "readers"
    required_args = {"standard": ["fnames"]}
    required_kwargs = {
        "standard": [
            "metadata_only",
            "chans",
            "area_def",
            "self_register",
        ],
    }

    def quick_view(self, fpaths):
        """Quickly extract dims, coords, and vars for the incoming files.

        Do so using xarray.open_dataset(fpath, chunks=None) to view the incoming file
        without actually loading its data into memory. This is used for the CLI command
        'geoips describe data'.

        Metadata can be collected from the file paths using
        <reader_plugin>(fpaths, metadata_only=True).

        Parameters
        ----------
        fpaths: list[str]
            - A list of absolute file paths to the incoming data.

        Returns
        -------
        data_dict: dict
            - A dictionary whose keys include ["coords", "dims", "variables"], of which
              the values corresponding to those keys are information about each
              coordinate, dimension, and variable.
        """
        variables = {}
        coords = {}
        dims = {}
        for fpath in fpaths:
            ds = open_dataset(fpath, chunks=None)
            for dim_key in ds.dims:
                dims[dim_key] = ds.dims[dim_key]
            for coord_key in ds.coords:
                coords[coord_key] = ds.coords[coord_key].attrs["long_name"]
            for var_key in ds.variables:
                variables[var_key] = ds.variables[var_key].attrs

        data_dict = {"Coordinates": coords, "Dimensions": dims, "Variables": variables}
        return data_dict


readers = ReadersInterface()
