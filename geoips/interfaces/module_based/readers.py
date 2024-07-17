# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface module."""

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
        {"METADATA": {"file0_METADATA": xarray_obj, ..., "fileX_METADATA": xarray_obj}}

        Parameters
        ----------
        all_metadata: list of xarray.Datasets
            - The incoming metadata from X number of files

        Returns
        -------
        concat_md: 2D dict of xarray Datasets
            - All metadata merged into a 2D dictionary of xarray Datasets
        """
        md = {"METADATA": {"source_file_attributes": {}}}
        for md_idx in range(len(all_metadata)):
            md["METADATA"]["source_file_attributes"][f"filename_{md_idx}"] = (
                all_metadata[md_idx]
            )
        return md


readers = ReadersInterface()
