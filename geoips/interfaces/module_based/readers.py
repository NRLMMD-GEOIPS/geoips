# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface module."""

import logging

from geoips.interfaces.base import BaseModuleInterface, BaseModulePlugin

LOG = logging.getLogger(__name__)


class BaseReadersPlugin(BaseModulePlugin):
    """Core class for all reader plugins.

    Includes shared attributes and methods which will be used to validate the output
    of your reader plugin.
    """

    xr_std_vars = set(["latitude", "longitude"])
    xr_std_md = set(
        [
            "source_name",
            "platform_name",
            "data_provider",
            "start_datetime",
            "end_datetime",
            "interpolation_radius_of_influence",
        ]
    )

    def _get_coords_dims_datasets_md(self, xobjs):
        """Extract dims, coords, datasets, and metadata for the incoming xobj[s].

        Parameters
        ----------
        xobjs: xarray object (xobj) or dict of xobjs
            - Incoming xarray objects from the current reader

        Returns
        -------
        data_dict: dict
            - A dictionary whose keys include ["coords", "dims", "variables"], of which
              the values corresponding to those keys are information about each
              coordinate, dimension, and variable.
        """
        self.variables = set([])
        self.coords = {}
        self.dims = {}
        self.metadata = {}

        if isinstance(xobjs, dict):
            # If xobjs is a dictionary of xarray objects, then loop over each key
            for key in xobjs:
                if key.lower() == "metadata":
                    md = True
                else:
                    md = False
                self._extract_data_single_xobj(xobjs[key], md=md)
        else:
            # Otherwise extract coords, dims, variables, and metadata from the provided
            # xarray object
            self._extract_data_single_xobj(xobjs, md=True)

        data_dict = {
            "Datasets": list(self.variables),
            "Coordinates": self.coords,
            "Dimensions": self.dims,
            "Metadata": self.metadata,
        }
        return data_dict

    def _extract_data_single_xobj(self, xobj, md):
        """Extract dims, coords, Datasets, and metadata for the incoming xobj[s].

        Metadata can be collected from the file paths using
        <reader_plugin>(fpaths, metadata_only=True).

        Parameters
        ----------
        xobj: dict[xobj] or xobj
            - Either a single xarray object or a dict of xarray objects
        md: bool
            - Whether or not the provided xobj comes from the 'METADATA' xobj
        """
        for dim_key in xobj.dims:
            self.dims[dim_key] = xobj.dims[dim_key]
        for coord_key in xobj.coords:
            if xobj.coords[coord_key].attrs.get("long_name"):
                self.coords[coord_key] = xobj.coords[coord_key].attrs["long_name"]
            else:
                self.coords[coord_key] = coord_key
        for var_key in xobj.variables:
            self.variables.add(var_key)
        if md:
            for md_key in xobj.attrs:
                if md_key.lower() == "file_metadata":
                    continue
                self.metadata[md_key] = xobj.attrs[md_key]

    def validate_output(self, xobjs):
        """Ensure the output of the reader plugin adheres to GeoIPS xarray standards.

        Match the data and metadata included in xobjs against required variables and
        required metadata for each reader.

        Parameters
        ----------
        xobjs: xarray object (xobj) or dict of xobjs
            - Incoming xarray objects from the current reader

        Returns
        -------
        valid_output: bool
            - Whether or not the information included in xobjs has all of the required
              metadata and variables.
        """
        xinfo_dict = self._get_coords_dims_datasets_md(xobjs)

        found_md = set(xinfo_dict["Metadata"].keys())
        found_vars = set(xinfo_dict["Datasets"])
        diff_md = self.xr_std_md.difference(found_md)
        diff_vars = self.xr_std_vars.difference(found_vars)

        missing_md = (
            f"Missing required metadata attributes {diff_md} in xarray object[s] "
            f"returned from {self.name}.\n"
        )
        missing_vars = (
            f"Missing required variables {diff_vars} in xarray object[s] "
            f"returned from {self.name}.\n"
        )
        if len(diff_md) or len(diff_vars):
            missing_str = ""
            if len(diff_md):
                missing_str += missing_md
            if len(diff_vars):
                missing_str += missing_vars
            LOG.interactive(missing_str)
            return False
        else:
            LOG.interactive(
                "Information in returned xarray objects adheres to GeoIPS xarray "
                "standards."
            )
            return True


class ReadersInterface(BaseModuleInterface):
    """Interface for ingesting a specific data type.

    Provides specification for ingensting a specific data type, and storing in
    the GeoIPS xarray-based internal format.
    """

    name = "readers"
    plugin_class = BaseReadersPlugin
    required_args = {"standard": ["fnames"]}
    required_kwargs = {
        "standard": [
            "metadata_only",
            "chans",
            "area_def",
            "self_register",
        ],
    }


readers = ReadersInterface()
