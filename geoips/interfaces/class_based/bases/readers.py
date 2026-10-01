# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Readers plugin class."""

import logging
import warnings
from pathlib import Path

import numpy as np
import xarray as xr

from geoips.utils.context_managers import import_optional_dependencies
from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.xarray_utils.coords import normalize_geoips_dataset_coords
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
