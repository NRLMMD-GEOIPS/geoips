# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers interface class."""

import collections
import logging
import warnings
from datetime import datetime
from os.path import basename
from pathlib import Path

import numpy as np
import xarray as xr
from xarray import concat, Dataset

from geoips.utils.context_managers import import_optional_dependencies
from geoips.errors import NoValidFilesError
from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.xarray_utils.coords import normalize_geoips_dataset_coords
from geoips.interfaces.base import BaseClassInterface
from geoips.plugins.classes.readers.utils.hrit_reader import HritError
from geoips.plugins.classes.readers.utils.geostationary_geolocation import (
    check_geolocation_cache_backend,
    get_geolocation_cache_filename,
    AutoGenError,
)

LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package & print to LOG.info if the import fails."""
    # If this reader is not installed on the system, don't fail alltogether,
    # just skip this import. This reader will not work if the import fails
    # and the package will have to be installed to process data of this type.
    import numexpr as ne
    import zarr

LOG = logging.getLogger(__name__)


class BaseReaderPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS reader plugins."""

    data_tree = False

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Strip injected upstream data for legacy (family-bearing) readers.

        Under OBP the workflow engine routes the entry step's input tree to the
        reader as ``data``. A legacy reader reads solely from ``filenames`` and its
        ``call`` does not accept a ``data`` argument, so the injected tree is
        dropped here (return ``None``); ``_invoke`` then calls the reader with
        ``filenames`` only. A Datatree-native reader (``data_tree=True``)
        keeps the tree via the standard pass-through in ``super()._pre_call``.
        """
        if _obp_initiated and not getattr(self, "data_tree", False):
            return None
        return super()._pre_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)

    def _normalize_obp_kwargs(self, kwargs):
        """Rename OBP reader kwargs for legacy readers.

        Legacy (family-bearing) reader plugins expect ``fnames`` in their
        ``call`` signature, but the OBP workflow interface uses ``filenames``.
        They also still expect ``chans`` while the OBP workflow interface uses
        ``variables``. This hook renames those kwargs so ``_obp_filter_kwargs``
        does not drop them and ``call`` receives the expected argument names.

        Datatree-native readers (no ``family``) pass through unchanged.
        """
        if not hasattr(self.__class__, "family"):
            return kwargs

        if "filenames" in kwargs:
            kwargs["fnames"] = kwargs.pop("filenames")

        if "chans" in kwargs:
            chans_message = (
                "'chans' is deprecated and will be removed in GeoIPS 2.0. Use"
                " 'variables' instead."
            )
            LOG.warning(chans_message)
            warnings.warn(chans_message, DeprecationWarning, stacklevel=2)
            kwargs.pop("variables", None)
        elif "variables" in kwargs:
            kwargs["chans"] = kwargs.pop("variables")

        return kwargs

    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Merge reader dict output into a ``DataTree`` for OBP.

        Readers return ``{key: xr.Dataset}``.  This hook merges the dict
        into a single ``xr.Dataset``, preserving ``METADATA`` attrs,
        and wraps the result in a plain ``xr.DataTree`` so downstream
        steps can access it via the standard tree-based data flow.
        """
        if _obp_initiated and isinstance(data, dict):
            metadata = data.pop("METADATA")
            root_ds = xr.Dataset()
            root_ds.attrs.update(metadata.attrs)
            dt = xr.DataTree(root_ds, name=getattr(self, "name", "reader"))
            for key, val in data.items():
                dt[key] = xr.DataTree(normalize_geoips_dataset_coords(val), name=key)
            return dt
        return super()._post_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)


class BaseAbiReaderPlugin(BaseReaderPlugin, abstract=True):
    """Base class for ABI-based readers."""

    # These should be added to the data file object
    BADVALS = {
        "Off_Of_Disk": -999.9,
        "Conditional": -999.8,
        "Out_Of_Valid_Range": -999.7,
        "No_Value": -999.6,
        "Uninitialized": -9999.9,
    }

    def _get_imager_projection(self, df):
        """Get imager projection."""
        gip = df.variables["goes_imager_projection"]
        metadata = {}
        md_names = [
            "inverse_flattening",
            "latitude_of_projection_origin",
            "longitude_of_projection_origin",
            "perspective_point_height",
            "semi_major_axis",
            "semi_minor_axis",
        ]
        for name in md_names:
            try:
                metadata[name] = getattr(gip, name)
                if metadata[name].size == 1:
                    metadata[name] = metadata[name][()]
            except AttributeError:
                LOG.info(
                    "Warning! Lat lon extent metadata field missing: {0}".format(name)
                )
        metadata["grid_mapping"] = getattr(gip, "grid_mapping_name")
        return metadata

    def _get_lat_lon_extent_metadata(self, df):
        """Get lat lon extent metadata."""
        glle = df.variables["geospatial_lat_lon_extent"]
        metadata = {}
        md_names = [
            "geospatial_eastbound_longitude",
            "geospatial_lat_center",
            "geospatial_lat_nadir",
            "geospatial_lon_center",
            "geospatial_lon_nadir",
            "geospatial_northbound_latitude",
            "geospatial_southbound_latitude",
            "geospatial_westbound_longitude",
        ]
        for name in md_names:
            try:
                metadata[name] = getattr(glle, name)
                if metadata[name].size == 1:
                    metadata[name] = metadata[name][()]
            except AttributeError:
                LOG.info(
                    "Warning! Lat lon extent metadata field missing: {0}".format(name)
                )
        return metadata

    def _get_variable_metadata(self, df):
        """
        Gather all required variable level metadata.

        Some are skipped or gathered later as needed.
        """
        metadata = {}
        # Note: We have skipped DQF, Rad, band_wavelength_star_look, num_star_looks,
        #       star_id, t, t_star_look, x_image, x_image_bounds, y_image,
        #       y_image_bounds, geospatial_lat_lon_extent, goes_imager_projection
        md_names = [
            "band_id",
            "band_wavelength",
            "earth_sun_distance_anomaly_in_AU",
            "esun",
            "kappa0",
            "max_radiance_value_of_valid_pixels",
            "min_radiance_value_of_valid_pixels",
            "missing_pixel_count",
            "nominal_satellite_height",
            "nominal_satellite_subpoint_lat",
            "nominal_satellite_subpoint_lon",
            "percent_uncorrectable_L0_errors",
            "planck_bc1",
            "planck_bc2",
            "planck_fk1",
            "planck_fk2",
            "processing_parm_version_container",
            "saturated_pixel_count",
            "std_dev_radiance_value_of_valid_pixels",
            "time_bounds",
            "undersaturated_pixel_count",
            "valid_pixel_count",
            "x",
            "y",
            "yaw_flip_flag",
        ]
        for name in md_names:
            try:
                metadata[name] = df.variables[name][...]
                if metadata[name].size == 1:
                    metadata[name] = metadata[name][()]
                if name in ["x", "y"]:
                    metadata[f"{name}_add_offset"] = df.variables[name].add_offset
                    metadata[f"{name}_scale_factor"] = df.variables[name].scale_factor
            except KeyError:
                LOG.info(
                    "Warning! Variable-level metadata field missing: {0}".format(name)
                )
        metadata["num_lines"] = metadata["y"].size
        metadata["num_samples"] = metadata["x"].size
        return metadata

    def _get_file_metadata(self, df):
        """Gather all of the file-level metadata."""
        metadata = {}
        md_names = [
            "id",
            "dataset_name",
            "naming_authority",
            "institution",
            "project",
            "iso_series_metadata_id",
            "Conventions",
            "Metadata_Conventions",
            "keywords_vocabulary",
            "standard_name_vocabulary",
            "title",
            "summary",
            "license",
            "keywords",
            "cdm_data_type",
            "orbital_slot",
            "platform_ID",
            "instrument_type",
            "processing_level",
            "date_created",
            "production_site",
            "production_environment",
            "production_data_source",
            "timeline_id",
            "scene_id",
            "spatial_resolution",
            "time_coverage_start",
            "time_coverage_end",
        ]
        metadata_dict = {"id": "instrument_ID"}
        for name in md_names:
            try:
                if hasattr(df, name):
                    metadata[name] = getattr(df, name)
                else:
                    metadata[name] = getattr(df, metadata_dict[name])
            except AttributeError:
                LOG.info("Warning! File-level metadata field missing: {0}".format(name))
        return metadata

    def _get_metadata(self, df, fname, **kwargs):
        """
        Gather metadata for the data file and return as a dictionary.

        Note: We are gathering all of the available metadata in case it is needed at
        some point.
        """
        metadata = {}
        # Gather all file-level metadata
        metadata["file_info"] = self._get_file_metadata(df)
        # Gather all variable-level metadata
        metadata["var_info"] = self._get_variable_metadata(df)
        # Gather lat lon extent info
        metadata["ll_info"] = self._get_lat_lon_extent_metadata(df)
        # Gather projection info
        metadata["projection"] = self._get_imager_projection(df)
        # Gather some useful info to the top level
        try:
            metadata["path"] = df.filepath()
        except ValueError:
            # Without cython installed, df.filepath() does not work
            metadata["path"] = fname
        metadata["satellite"] = metadata["file_info"]["platform_ID"]
        metadata["sensor"] = "ABI"
        metadata["num_lines"] = metadata["var_info"]["y"].size
        metadata["num_samples"] = metadata["var_info"]["x"].size
        return metadata

    def _get_geolocation_metadata(self, metadata):
        """
        Gather all of the metadata used in creating geolocation data for input file.

        This is split out so we can easily create a cache of the data for creation
        of a unique filename. This allows us to avoid recalculation of angles that
        have already been calculated.
        """
        geomet = {}
        # G16 -> goes-16
        geomet["platform_name"] = metadata["file_info"]["platform_ID"].replace(
            "G", "goes-"
        )
        geomet["Re"] = metadata["projection"]["semi_major_axis"]
        geomet["Rp"] = metadata["projection"]["semi_minor_axis"]
        geomet["invf"] = metadata["projection"]["inverse_flattening"]
        geomet["e"] = 0.0818191910435
        geomet["pphgt"] = metadata["projection"]["perspective_point_height"]
        geomet["H_m"] = geomet["Re"] + geomet["pphgt"]
        geomet["lat0"] = metadata["projection"]["latitude_of_projection_origin"]
        geomet["lon0"] = metadata["projection"]["longitude_of_projection_origin"]
        geomet["scene"] = metadata["file_info"]["scene_id"]
        # Just getting the nadir resolution in kilometers.  Must extract from a string.
        geomet["res_km"] = float(
            metadata["file_info"]["spatial_resolution"].split()[0][0:-2]
        )
        geomet["roi_factor"] = 5  # roi = res * roi_factor, was 10
        geomet["num_lines"] = metadata["var_info"]["num_lines"]
        geomet["num_samples"] = metadata["var_info"]["num_samples"]
        geomet["x"] = metadata["var_info"]["x"]
        geomet["y"] = metadata["var_info"]["y"]
        return geomet

    def get_latitude_longitude(
        self,
        metadata,
        BADVALS,
        sect=None,
        geolocation_cache_backend="memmap",
        chunk_size=None,
        resource_tracker=None,
    ):
        """
        Get latitudes and longitudes.

        This routine accepts a dictionary containing metadata as read from a NCDF4
        format file, and returns latitudes and longitudes for a full disk.
        """
        check_geolocation_cache_backend(geolocation_cache_backend)
        # If the filename format needs to change for the pre-generated geolocation
        # files, please discuss prior to changing.  It will force recreation of all
        # files, which can be problematic for large numbers of sectors
        fname = get_geolocation_cache_filename(
            "GEOLL",
            metadata,
            geolocation_cache_backend=geolocation_cache_backend,
            chunk_size=chunk_size,
        )
        if resource_tracker is not None:
            key = Path(fname).name
            if sect:
                key += f"_{sect.area_id}"
            resource_tracker.track_resource_usage(
                logstr="MEMUSG", verbose=False, key=key
            )
        if not Path(fname).exists():
            if (
                sect is not None
                and self.DONT_AUTOGEN_GEOLOCATION
                and "tc2019" not in sect.name
            ):
                msg = (
                    f"GETGEO Requested NO AUTOGEN GEOLOCATION. "
                    f"Could not create latlonfile for ad {metadata['scene']}: {fname}"
                )
                LOG.error(msg)
                raise AutoGenError(msg)

            LOG.debug("Calculating latitudes and longitudes.")

            r2d = 180.0 / np.pi  # NOQA

            lambda0 = np.radians(metadata["lon0"])  # NOQA
            Re = metadata["Re"]
            # invf = metadata['invf']
            Rp = metadata["Rp"]
            # e = np.sqrt((1 / invf) * (2 - 1 / invf))
            H = metadata["H_m"]
            c = H**2 - Re**2  # NOQA

            # Python 3 netcdf reads create a masked array, while Python 2 netcdf reads
            # create ndarray. These should NOT be masked, so if we have a masked array,
            # fill it.
            if isinstance(metadata["x"], np.ma.core.MaskedArray):
                x = np.float64(metadata["x"].filled())
            else:
                x = np.float64(metadata["x"])
            if isinstance(metadata["y"], np.ma.core.MaskedArray):
                y = np.float64(metadata["y"].filled())
            else:
                y = np.float64(metadata["y"])

            LOG.info("      Making {0} by {1} grid.".format(x.size, y.size))
            # Need to transpose the latline, then repeat lonsize times
            yT = y[np.newaxis].T
            y = np.hstack([yT for num in range(x.size)])
            # Repeat lonline latsize times
            x = np.vstack([x for num in range(yT.size)])

            # Note: In this next section, we will be reusing memory space as much as
            #       possible. To make this as transparent as possible, we will do all
            #       variable assignment first, then fill them
            # This method requires that all lines remain in the SAME ORDER or things
            # will go very badly
            cosx = np.empty_like(x)
            cosy = np.empty_like(x)
            a = np.empty_like(x)
            b = np.empty_like(x)
            sinx = x  # X is not needed after the line that defines sinx
            siny = y  # Y is not needed after the line that defines siny
            rs = a
            sx = b
            sy = cosy  # sinx is not needed after the line that defines sy
            sz = cosx  # cosx is not needed after the line that defines sz
            lats = rs
            lons = sz

            LOG.info("      Calculating intermediate steps")
            Rrat = Re**2 / Rp**2  # NOQA
            ne.evaluate("cos(x)", out=cosx)  # NOQA
            ne.evaluate("cos(y)", out=cosy)  # NOQA
            ne.evaluate("sin(x)", out=sinx)  # NOQA
            ne.evaluate("sin(y)", out=siny)  # NOQA
            ne.evaluate("sinx**2 + cosx**2 * (cosy**2 + siny**2 * Rrat)", out=a)  # NOQA
            ne.evaluate("-2 * H * cosx * cosy", out=b)  # NOQA
            ne.evaluate("(-b - sqrt(b**2 - (4 * a * c))) / (2 * a)", out=rs)  # NOQA
            good_mask = np.isfinite(rs)

            ne.evaluate("rs * cosx * cosy", out=sx)  # NOQA
            ne.evaluate("rs * cosx * siny", out=sz)  # NOQA
            ne.evaluate("rs * sinx", out=sy)  # NOQA

            LOG.info("Calculating Latitudes")
            ne.evaluate("r2d * arctan(Rrat * sz / sqrt((H - sx)**2 + sy**2))", out=lats)
            LOG.info("Calculating Longitudes")
            lons = ne.evaluate("r2d * (lambda0 + arctan(sy / (H - sx)))", out=lons)
            lats[~good_mask] = BADVALS["Off_Of_Disk"]
            lons[~good_mask] = BADVALS["Off_Of_Disk"]
            LOG.info("Done calculating latitudes and longitudes")

            if geolocation_cache_backend == "memmap":
                with open(fname, "w") as df:
                    lats.tofile(df)
                    lons.tofile(df)
            elif geolocation_cache_backend == "zarr":
                if chunk_size:
                    chunks = (chunk_size, chunk_size)
                else:
                    chunks = None
                LOG.info("Storing to %s (chunks=%s)", fname, chunks)
                # zarr does NOT have a close method, so you can NOT use the with context
                zf = zarr.open(fname, mode="w")
                # Assume both arrays have the same shape and dtype
                kwargs = {
                    "shape": lats.shape,
                    "dtype": lats.dtype,
                }
                # As of Python 3.11, can't pass chunks=None into create_dataset
                if chunks:
                    kwargs["chunks"] = chunks
                zf.create_dataset("lats", **kwargs)
                zf.create_dataset("lons", **kwargs)
                zf["lats"][:] = lats
                zf["lons"][:] = lons
            # # Possible switch to xarray based geolocation files, but we lose
            # memmapping.
            # ds = xarray.Dataset(
            #     {
            #         'latitude':(['x','y'],lats),
            #         'longitude':(['x','y'],lons)
            #         }
            #     )
            # ds.to_netcdf(fname)
        else:
            # Create memmap to the lat/lon file
            # Nothing will be read until explicitly requested
            # We are mapping this here so that the lats and lons are available when
            # calculating satellite angles
            if geolocation_cache_backend == "memmap":
                shape = (metadata["num_lines"], metadata["num_samples"])
                offset = 8 * metadata["num_samples"] * metadata["num_lines"]
                lats = np.memmap(
                    fname, mode="r", dtype=np.float64, offset=0, shape=shape
                )
                lons = np.memmap(
                    fname, mode="r", dtype=np.float64, offset=offset, shape=shape
                )
            elif geolocation_cache_backend == "zarr":
                LOG.info(
                    "GETGEO zarr to {} : lat/lon file for {}".format(
                        fname, metadata["scene"]
                    )
                )
                # zarr does NOT have a close method, so you can NOT use the with context
                zf = zarr.open(fname, mode="r")
                lats = zf["lats"]
                lons = zf["lons"]
        # Possible switch to xarray based geolocation files, but we lose memmapping
        # saved_xarray = xarray.load_dataset(fname)
        # lons = saved_xarray['longitude'].to_masked_array()
        # lats = saved_xarray['latitude'].to_masked_array()
        if resource_tracker is not None:
            resource_tracker.track_resource_usage(
                logstr="MEMUSG", verbose=False, key=key
            )

        return lats, lons


class ReadersInterface(BaseClassInterface):
    """Interface for ingesting a specific data type.

    Provides specification for ingensting a specific data type, and storing in
    the GeoIPS xarray-based internal format.
    """

    name = "readers"
    plugin_class = BaseReaderPlugin

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
        **kwargs,
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
        if not self.unique_stimes:
            raise NoValidFilesError(
                f"No valid files found out of {len(fnames)} provided. "
                f"Requested channels: {chans}. "
                "Ensure files and channels match the reader's expectations."
            )
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
            **kwargs,
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
        **kwargs,
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
                **kwargs,
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
