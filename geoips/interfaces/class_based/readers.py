# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface class."""

import collections
from datetime import datetime
from os.path import basename

import numpy as np
from xarray import concat, Dataset

from geoips.errors import NoValidFilesError
from geoips.interfaces.base import BaseClassInterface
from geoips.plugins.modules.readers.utils.hrit_reader import HritError


class ReadersInterface(BaseClassInterface):
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
        read_single_time_func,
        metadata_only=False,
        chans=None,
        area_def=None,
        self_register=False,
        **kwargs
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
        read_single_time_func : python function
            * Function which can be used to read a single scan time of files from a
              reader plugin.
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
        # Sort fnames. This should sort them by time and channel more often than not.
        fnames = sorted(fnames)
        # We really only need to get the start time from all of these files. I wish
        # there were an easier and more efficient route, but this should work for the
        # time being. Personally, I think it'd be a good idea to add a new argument to
        # this method that accepts a function which calculates the start datetime of
        # all files provided.
        all_file_metadata = []
        updated_fnames = []
        for x in fnames:
            try:
                all_file_metadata.append(
                    read_single_time_func(
                        [x],
                        metadata_only=True,
                        chans=chans,
                    )["METADATA"]
                )
                updated_fnames += [x]
            except NoValidFilesError:
                # If the current file is not valid, just skip this one.
                # print(f"{str(e)}: No files found, skipping")
                continue
            except (ValueError, HritError) as e:
                # Value error is raised for 'inconsistent' metadata, or in this case
                # No appropriate file for the channels selected
                if isinstance(e, ValueError):
                    st = None
                    et = None
                else:
                    """
                    This occurs from the seviri_hrit reader in 'get_top_level_metadata'
                    Parse out the start and end datetimes, as this file still could be
                    Relevant, but is missing 'block_2'. If the set of files all are
                    missing block_2, or the projection of block_2 is not GEOS, it will
                    cause an HritError in the for loop before, which doesn't have a try
                    except statement.

                    Error Format:
                    f"Unknown projection encountered: {projection}.\n"
                    f"start_datetime={st.isoformat()}\n"
                    f"end_datetime={et.isoformat()}"
                    """
                    emsg = str(e).split("\n")
                    # Recreate the datetime objects from the isoformat strings provided
                    st = datetime.fromisoformat(emsg[1].split("=")[1])
                    et = datetime.fromisoformat(emsg[2].split("=")[1])
                # Add st, et as datetimes for the file, nonetheless if they are None
                # or a valid datetime
                all_file_metadata.append(
                    Dataset(attrs=dict(start_datetime=st, end_datetime=et))
                )
                updated_fnames += [x]
        self.start_times = [md.attrs["start_datetime"] for md in all_file_metadata]
        self.end_times = [md.attrs["end_datetime"] for md in all_file_metadata]

        # Get unique start times and end times. We do this by initally creating a set
        # from all found start and end times. Keep in mind, some of these times could
        # be 'None' if a value error is raised from the reader call function. This
        # occurs when none of the selected channels were found in the file provided.
        # Meaning, we don't need that file..
        # Now, remove 'None' from the set (the files the don't need). This leaves a list
        # of unique file times that have been found in datasets that contain the correct
        # channels.
        self.unique_stimes = list(set(self.start_times).difference(set([None])))
        self.unique_etimes = list(set(self.end_times).difference(set([None])))
        # Set these values to this class so they can be used downstream for reading
        # data from the correct time steps
        metadata_by_scan_time = []
        for stime in self.unique_stimes:
            # Get the indices of all files which match the current start time
            same_scan_time_files = [dt == stime for dt in self.start_times]
            # Now get the metadata of all of the files which match that time
            metadata_by_scan_time.append(
                read_single_time_func(
                    list(np.array(updated_fnames)[same_scan_time_files]),
                    metadata_only=True,
                    chans=chans,
                )["METADATA"]
            )
        all_metadata = self.concatenate_metadata(metadata_by_scan_time)
        if metadata_only:
            return all_metadata

        dict_xarrays = self.call_files_and_get_top_level_metadata(
            updated_fnames,
            all_metadata,
            read_single_time_func,
            metadata_only,
            chans,
            area_def,
            self_register,
            **kwargs
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
            md["METADATA"].attrs["source_file_names"] += [
                basename(x) for x in all_metadata[md_idx].attrs["source_file_names"]
            ]
            md["METADATA"].attrs["source_file_datetimes"].append(
                [
                    all_metadata[md_idx].start_datetime,
                    all_metadata[md_idx].end_datetime,
                ],
            )
            for x in all_metadata[md_idx].attrs["source_file_names"]:
                md["METADATA"].attrs["source_file_attributes"][basename(x)] = (
                    all_metadata[md_idx]
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
        **kwargs
    ):
        """
        Read in data from a list of filenames.

        Parameters
        ----------
        fnames : list
            * List of strings, full paths to files
        all_metadata : dict
            * Dictionary of metadata from all files in 'fnames'
        read_single_time_func : python function
            * Function which can be used to read a single scan time of files from a
              reader plugin.
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
        ingested_xarrays = collections.defaultdict(list)
        for time in self.unique_stimes:
            scan_time_files = [dt == time for dt in self.start_times]
            # Call the associated reader for a series of files associated with the same
            # scan time
            data_dict = call_single_file_func(
                list(np.array(fnames)[scan_time_files]),
                metadata_only=metadata_only,
                chans=chans,
                area_def=area_def,
                self_register=self_register,
                **kwargs
            )
            for (
                dname,
                dset,
            ) in data_dict.items():
                ingested_xarrays[dname].append(dset)

        if len(self.unique_stimes) == 1:
            # No need to stack if we are only reading in one scan time
            # This is likely temporary to maintain backwards compatibility

            # This is not hit if we are provided multiple scan times.
            return data_dict

        # Now that we've ingested all scan times, stack along time dimension
        metadata = all_metadata["METADATA"]
        dict_xarrays = {}
        for dname, list_xarrays in ingested_xarrays.items():
            if dname == "METADATA":
                continue
            merged_dset = concat(list_xarrays, dim="time")
            merged_dset.attrs["start_datetime"] = min(self.unique_stimes)
            merged_dset.attrs["end_datetime"] = max(self.unique_etimes)
            merged_dset = merged_dset.assign_coords({"time": self.unique_stimes})
            dict_xarrays[dname] = merged_dset
            # Override source_file_* attributes with what's set in all_metadata.
            dict_xarrays[dname].attrs["source_file_names"] = metadata.attrs[
                "source_file_names"
            ]
            dict_xarrays[dname].attrs["source_file_attributes"] = metadata.attrs[
                "source_file_attributes"
            ]
            dict_xarrays[dname].attrs["source_file_datetimes"] = metadata.attrs[
                "source_file_datetimes"
            ]

        metadata.attrs["start_datetime"] = min(self.unique_stimes)
        metadata.attrs["end_datetime"] = max(self.unique_etimes)
        dict_xarrays["METADATA"] = metadata

        return dict_xarrays


readers = ReadersInterface()
