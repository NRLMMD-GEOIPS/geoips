# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface module."""

from os.path import basename

import numpy as np
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

    def read_data_to_xarray_dict(
        self,
        fnames,
        call_single_file_func,
        metadata_only=False,
        chans=None,
        area_def=None,
        self_register=False,
    ):
        """Read in data potentially from multiple scan times into an xarray dict.

        This function does not require that you provide multiple scan times, but allows
        for that in the case those are provided.

        Call this with information specific to your reader to generate a dictionary of
        xarray datasets created from the data provided in 'fnames'.

        Parameters
        ----------
        fnames : list
            * List of strings, full paths to files
        all_metadata : dict
            * Dictionary of metadata from all files in 'fnames'
        call_single_file_func : python function
            * Function which can be used to read a single file from a reader plugin.
            * Most likely named 'call_single_time'.
        metadata_only : bool, default=False
            * Return before actually reading data if True
        chans : list of str, default=None
            * List of desired channels (skip unneeded variables as needed).
            * Include all channels if None.
        area_def : pyresample.AreaDefinition, default=None
            * Specify region to read
            * Read all data if None.
        self_register : str or bool, default=False
            * register all data to the specified dataset id (as specified in the
              return dictionary keys).
            * Read multiple resolutions of data if False.

        Returns
        -------
        dict of xarray.Datasets
            * dictionary of xarray.Dataset objects with required Variables and
              Attributes.
            * Dictionary keys can be any descriptive dataset ids.

        See Also
        --------
        :ref:`xarray_standards`
            Additional information regarding required attributes and variables
            for GeoIPS-formatted xarray Datasets.
        """
        all_metadata = self.concatenate_metadata(
            [call_single_file_func([x], metadata_only=True)["METADATA"] for x in fnames]
        )
        if metadata_only:
            return all_metadata

        dict_xarrays = self.call_files_and_get_top_level_metadata(
            fnames,
            all_metadata,
            call_single_file_func,
            metadata_only,
            chans,
            area_def,
            self_register,
        )
        return dict_xarrays

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

        for md_idx in range(len(all_metadata)):
            # Set required attributes of the top-level metadata when this loop is
            # started
            if md_idx == 0:
                md["METADATA"].attrs = all_metadata[md_idx].attrs
                md["METADATA"].attrs["source_file_names"] = []
                md["METADATA"].attrs["source_file_attributes"] = {}
                md["METADATA"].attrs["source_file_datetimes"] = []
                md["METADATA"].attrs["end_datetime"] = all_metadata[-1].end_datetime

            # Add to optional attributes of the top-level metadata for each xobj
            # provided
            fname = all_metadata[md_idx].attrs["source_file_names"][0]
            md["METADATA"].attrs["source_file_names"].append(basename(fname))
            md["METADATA"].attrs["source_file_attributes"][basename(fname)] = (
                all_metadata[md_idx]
            )
            md["METADATA"].attrs["source_file_datetimes"].append(
                all_metadata[md_idx].start_datetime
            )

        return md

    def call_files_and_get_top_level_metadata(
        self,
        fnames,
        all_metadata,
        call_single_file_func,
        metadata_only=False,
        chans=None,
        area_def=None,
        self_register=False,
    ):
        """
        Read in data from a list of filenames.

        Parameters
        ----------
        fnames : list
            * List of strings, full paths to files
        all_metadata : dict
            * Dictionary of metadata from all files in 'fnames'
        call_single_file_func : python function
            * Function which can be used to read a single file from a reader plugin.
            * Most likely named 'call_single_time'.
        metadata_only : bool, default=False
            * Return before actually reading data if True
        chans : list of str, default=None
            * List of desired channels (skip unneeded variables as needed).
            * Include all channels if None.
        area_def : pyresample.AreaDefinition, default=None
            * Specify region to read
            * Read all data if None.
        self_register : str or bool, default=False
            * register all data to the specified dataset id (as specified in the
              return dictionary keys).
            * Read multiple resolutions of data if False.

        Returns
        -------
        dict of xarray.Datasets
            * dictionary of xarray.Dataset objects with required Variables and
              Attributes.
            * Dictionary keys can be any descriptive dataset ids.

        See Also
        --------
        :ref:`xarray_standards`
            Additional information regarding required attributes and variables
            for GeoIPS-formatted xarray Datasets.
        """
        start_times = [
            dt for dt in all_metadata["METADATA"].attrs["source_file_datetimes"]
        ]
        times = list(set(start_times))
        import collections

        ingested_xarrays = collections.defaultdict(list)
        for time in times:
            scan_time_files = [dt == time for dt in start_times]
            # Call the associated reader for a single file
            data_dict = call_single_file_func(
                np.array(fnames)[scan_time_files],
                metadata_only=metadata_only,
                chans=chans,
                area_def=area_def,
                self_register=self_register,
            )
            for (
                dname,
                dset,
            ) in data_dict.items():
                ingested_xarrays[dname].append(dset)

        if len(times) == 1:
            # No need to stack if we are only reading in one scan time
            # This is likely temporary to maintain backwards compatibility

            # This is not hit if we are provided multiple scan times.
            return data_dict

        import xarray

        # merged_dset = xarray.Dataset()
        # Now that we've ingested all scan times, stack along time dimension
        metadata = all_metadata["METADATA"]
        dict_xarrays = {}
        for dname, list_xarrays in ingested_xarrays.items():
            if dname == "METADATA":
                continue
            merged_dset = xarray.concat(list_xarrays, dim="time_dim")
            merged_dset.attrs["start_datetime"] = min(times)
            merged_dset.attrs["end_datetime"] = max(times)
            merged_dset = merged_dset.assign_coords({"time_dim": times})
            dict_xarrays[dname] = merged_dset
            # Override source_file_names what's set in all_metadata. That includes
            # all files provided to the reader.
            dict_xarrays[dname].attrs["source_file_names"] = metadata.attrs[
                "source_file_names"
            ]
            dict_xarrays[dname].attrs["source_file_attributes"] = metadata.attrs[
                "source_file_attributes"
            ]
            dict_xarrays[dname].attrs["source_file_datetimes"] = metadata.attrs[
                "source_file_datetimes"
            ]

        metadata.attrs["start_datetime"] = min(times)
        metadata.attrs["end_datetime"] = max(times)
        dict_xarrays["METADATA"] = metadata

        return dict_xarrays


readers = ReadersInterface()
