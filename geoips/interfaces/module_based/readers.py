# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface module."""

from os.path import basename
from xarray import Dataset

from geoips.interfaces.base import BaseModuleInterface


class ReadersInterface(BaseModuleInterface):
    """Interface for ingesting a specific data type.

    Provides specification for ingensting a specific data type, and storing in
    the GeoIPS xarray-based internal format.
    """

    name = "readers"
    required_args = {"standard": ["fnames"]}
    required_kwargs = {
        "standard": ["metadata_only", "chans", "area_def", "self_register"]
    }

    def concatenate_metadata(self, all_metadata):
        """Merge together metadata sourced from a list of files into one dictionary.

        Where the structure of the merged metadata is a nested dictionary of metadata.

        Ie. (xarray_obj has no data and is merely just a container for metadata):
        {"METADATA": xobj.source_file_attributes: {fname: xobj, ..., "fnamex": xobj}}

        Parameters
        ----------
        all_metadata: list of xarray.Datasets
            - The incoming metadata from X number of files

        Returns
        -------
        md: dict of xarray Datasets
            - All metadata merged into a dictionary of xarray Datasets
        """
        md = {"METADATA": Dataset()}
        source_file_names_missing = False

        for md_idx in range(len(all_metadata)):
            if md_idx == 0:
                md["METADATA"].attrs = all_metadata[md_idx].attrs
                md["METADATA"].attrs["source_file_attributes"] = {}
                md["METADATA"].attrs["source_file_datetimes"] = []
                md["METADATA"].attrs["end_datetime"] = all_metadata[-1].end_datetime

            fname = all_metadata[md_idx].attrs["source_file"]
            md["METADATA"].attrs["source_file_attributes"][basename(fname)] = (
                all_metadata[md_idx]
            )
            md["METADATA"].attrs["source_file_datetimes"].append(
                all_metadata[md_idx].start_datetime
            )

            if "source_file_names" not in md["METADATA"].attrs.keys():
                # This hasn't already been added and we need to create this attribute
                source_file_names_missing = True
                md["METADATA"].attrs["source_file_names"] = []
            if source_file_names_missing:
                # No source file names found initially, make sure to add those files
                # to this attribute. The length of this should match the length of both
                # source_file_attributes and source_file_datetimes
                md["METADATA"].attrs["source_file_names"].append(basename(fname))

        return md


readers = ReadersInterface()
