# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Generalized geolocation calculations for geostationary satellites."""

import os
from datetime import datetime
import logging
import numpy as np
from pathlib import Path
from pyresample import utils
from pyresample.geometry import SwathDefinition
from pyresample.kd_tree import get_neighbour_info  # , get_sample_from_neighbour_info
import time
import zarr

from geoips.errors import CoverageError
from geoips.filenames.base_paths import PATHS as gpaths
from geoips.utils.context_managers import import_optional_dependencies

LOG = logging.getLogger(__name__)

# interface = None indicates to the GeoIPS interfaces that this is not a valid
# plugin, and this module will not be added to the GeoIPS plugin registry.
# This allows including python modules within the geoips/plugins directory
# that provide helper or utility functions to the geoips plugins, but are
# not full GeoIPS plugins on their own.
interface = None

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import numexpr as ne


nprocs = 6

try:
    ne.set_num_threads(nprocs)
except Exception:
    LOG.info(
        "Failed numexpr.set_num_threads in %s. If numexpr is not installed and you "
        "need it, install it.",
        __file__,
    )

DONT_AUTOGEN_GEOLOCATION = gpaths["DONT_AUTOGEN_GEOLOCATION"]

STATIC_GEOLOCDIR = gpaths["GEOIPS_DATA_CACHE_DIR_LONGTERM_GEOLOCATION_STATIC"]

# default dynamic geoloc dir for NRL
DYNAMIC_GEOLOCDIR = gpaths["GEOIPS_DATA_CACHE_DIR_LONGTERM_GEOLOCATION_DYNAMIC"]

READ_GEOLOCDIRS = (
    gpaths["READ_GEOLOCDIRS"].split(":") if gpaths["READ_GEOLOCDIRS"] else []
)


class AutoGenError(Exception):
    """Raise exception on auto generated geolocation error."""

    pass


class CachedGeolocationIndexError(IndexError):
    """Raise exception on cached geolocation IndexError."""

    pass


class CacheNotFoundError(FileNotFoundError):
    """Raise exception if cached data is not found."""

    pass


def check_geolocation_cache_backend(
    cache_backend, supported_backends=("memmap", "zarr")
):
    """Check if requested geolocation cache backend is supported.

    Perhaps this should be converted to a decorator later on?

    Parameters
    ----------
    cache_backend : str
        Library name used to create cached geolocation files (e.g. zarr or memmap)
    supported_backends : list or tuple, optional
        Supported cache backends, by default ("memmap", "zarr")

    Raises
    ------
    ValueError
        If cache_backend is not in supported_backends
    """
    if cache_backend not in supported_backends:
        raise ValueError(
            f"Unsupported cache backend: {cache_backend}."
            f" Supported cache backends: {supported_backends}"
        )


def construct_cache_filename(
    pref, metadata, area_def=None, cache_backend="memmap", chunk_size=None
):
    """Construct a cached file name.

    Parameters
    ----------
    pref : str
        Prefix to identify type of cached data
    metadata : dict
        Top level metadata for dataset
    area_def : pyresample.area_definition, optional
        Area definition subsector of data, by default None
    cache_backend : str, optional
        Specify to use either numpy.memmao or zarray for cache, by default "memmap"
    chunk_size : int, optional
        zarray cache chunk size, by default None

    Returns
    -------
    str
        File name for cached data
    """
    check_geolocation_cache_backend(cache_backend)
    # In order to ensure consistency here, take a sha1 hash of the string representation
    #  of the dictionary values. hash is applied to the object itself, which appears to
    # not be consistent from one Python 3 run to the next.
    # The dictionary values themselves (sorted) SHOULD be consistent between runs.
    from hashlib import sha1

    metadata_string = ""
    for mkey in sorted(metadata.keys()):
        if mkey == "start_datetime":
            continue
        metadata_string += str(metadata[mkey])
    md_hash = sha1(metadata_string.encode("ascii"), usedforsecurity=False).hexdigest()
    # md_hash = hash(frozenset((k, v) for k, v in metadata.items()
    #                                                      if isinstance(v, Hashable)))

    fname = "{}_{}_{}x{}".format(
        pref,
        metadata["scene"],
        metadata["num_lines"],
        metadata["num_samples"],
    )
    if cache_backend != "memmap":
        # Only replace whitespaces with a hyphen when not memmap to prevent regenerating
        # any cached geolocation files
        fname = fname.replace(" ", "-")

    if chunk_size and cache_backend == "zarr":
        # If chunking enabled, include the size in the file name
        fname += f"_chunk{chunk_size}"

    # If the filename format needs to change for the pre-generated geolocation
    # files, please discuss prior to changing.  It will force recreation of all
    # files, which can be problematic for large numbers of sectors

    if area_def:
        ad = area_def
        LOG.info("Using area_definition information ")
        LOG.info(
            "    Using area_definition information for hash: "
            + str(ad.proj_dict.items())
        )
        # sector_hash = hash(frozenset(ad.proj_dict.items()))
        from hashlib import sha1

        metadata_string = ""
        for mkey in sorted(ad.proj_dict.keys()):
            # We don't want to include start/end datetimes in metadata hash!!
            if mkey == "start_datetime":
                continue
            metadata_string += str(ad.proj_dict[mkey])
        sector_hash = sha1(
            metadata_string.encode("ascii"), usedforsecurity=False
        ).hexdigest()
        sect_nlines = ad.shape[0]
        sect_nsamples = ad.shape[1]
        sect_clat = area_def.proj_dict["lat_0"]
        sect_clon = area_def.proj_dict["lon_0"]
        fname += "_{}_{}x{}_{}x{}".format(
            area_def.area_id, sect_nlines, sect_nsamples, sect_clat, sect_clon
        )
        fname += "_{}_{}".format(md_hash, sector_hash)
    else:
        fname += "_{}".format(md_hash)

    if cache_backend == "memmap":
        fname += ".dat"
    elif cache_backend == "zarr":
        fname += ".zarr"
    return fname


def get_data_cache_filename(
    pref,
    metadata,
    area_def=None,
    cache_backend="memmap",
    chunk_size=None,
    scan_datetime=None,
):
    """Get the full file path for a cached calibrated data file.

    Parameters
    ----------
    pref : str
        Prefix to identify type of cached data
    metadata : dict
        Top level metadata for dataset
    area_def : pyresample.area_definition, optional
        Area definition subsector of data, by default None
    cache_backend : str, optional
        Specify to use either numpy.memmao or zarray for cache, by default "memmap"
    chunk_size : int, optional
        zarray cache chunk size, by default None

    Returns
    -------
    str
       Full file path for cached data
    """
    cache_dir = os.path.join(
        gpaths["GEOIPS_DATA_CACHE_DIR_SHORTTERM_CALIBRATED_DATA"],
    )
    if scan_datetime is not None:
        pref += f"_{scan_datetime.strftime('%Y%m%dT%H%M%S.%fZ')}"
    if not os.path.isdir(cache_dir):
        try:
            os.makedirs(cache_dir)
        except FileExistsError:
            pass
    fname = construct_cache_filename(
        pref,
        metadata,
        area_def=area_def,
        cache_backend=cache_backend,
        chunk_size=chunk_size,
    )
    return os.path.join(cache_dir, metadata["platform_name"], fname)


def get_geolocation_cache_filename(
    pref,
    metadata,
    area_def=None,
    geolocation_cache_backend="memmap",
    chunk_size=None,
    solar_angles=False,
):
    """Set the location and filename format for the cached geolocation files.

    There is a separate filename format for satellite latlons and sector latlons

    Notes
    -----
    Changing geolocation filename format will force recreation of all
    files, which can be problematic for large numbers of sectors.
    """
    if solar_angles:
        cache = os.path.join(
            gpaths["GEOIPS_DATA_CACHE_DIR_SHORTTERM_GEOLOCATION_SOLAR_ANGLES"],
            metadata["platform_name"],
        )
    else:
        cache = os.path.join(STATIC_GEOLOCDIR, metadata["platform_name"])
        from geoips.sector_utils.utils import is_dynamic_sector

        if is_dynamic_sector(area_def):
            cache = os.path.join(DYNAMIC_GEOLOCDIR, metadata["platform_name"])
    if not os.path.isdir(cache):
        try:
            os.makedirs(cache)
        except FileExistsError:
            pass

    fname = construct_cache_filename(
        pref,
        metadata,
        area_def=area_def,
        cache_backend=geolocation_cache_backend,
        chunk_size=chunk_size,
    )

    # Check alternative read-only directories (i.e. operational)
    for dirname in READ_GEOLOCDIRS:
        if os.path.exists(os.path.join(dirname, metadata["platform_name"], fname)):
            return os.path.join(dirname, metadata["platform_name"], fname)

    # If not found, return the normal cached filename
    return os.path.join(cache, fname)


def check_for_partial_cache(
    cache_filename, partial_cache_filename, cache_timeout_seconds=30
):
    """Check if a partial data cache exists.

    These partial (temporary) caches are created when the cache is being created, and is
    renamed once complete. If a partial cache is found, try for 30 seconds (default) to
    see if it is renamed to the final cache_filename

    Parameters
    ----------
    cache_filename : str
        Full path to complete cache
    partial_cache_filename : str
        Full path to temporary/partial cache
    cache_timeout_seconds : int, optional
        Retry window to check for final cache if a partial cache is found, by default 30

    Raises
    ------
    CacheNotFoundError
        If cache_filename is not found after retry window
    """
    no_coverage_cache = partial_cache_filename.replace("partial", "no_coverage")
    if Path(partial_cache_filename).exists():
        LOG.info("Found partial cache: %s", partial_cache_filename)
        LOG.info("Will attempt to re-check for complete cache")
        start_time = datetime.now()
        partial_exists = Path(partial_cache_filename).exists()
        while partial_exists:
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            if elapsed_seconds < cache_timeout_seconds:
                LOG.debug("Partial cache still exists, will check again in 1 second")
                time.sleep(1)
            else:
                LOG.error(
                    "Exceeded cache timeout of %s seconds."
                    " If problem persists, delete %s",
                    cache_timeout_seconds,
                    partial_cache_filename,
                )
                partial_exists = False
    if Path(no_coverage_cache).exists():
        # This will potentially cause an issue specifically for dynamic sectors with
        # interpolated positions where the initial position (ie, storm location at 0Z)
        # is outside satellite coverage, but a later interpolated position (e.g.,
        # interpolated location at 5Z) may have coverage. We are going to accept this
        # case, because the interpolated location will likely still be at edge of scan.
        # Per images below, for TCs in particular, I really don't think we care about
        # this, since they don't move much in 6h and I can't imagine we wouldn't want
        # something at 0Z, but then would want it at 5Z.

        # Note there may be future cases where we would not want to accept this risk, if
        # a dynamic sector moves very quickly, and intermediate interpolated locations
        # could vary drastically from the reported positions at specific times.
        LOG.info("Cache flagged as having no coverage: %s", no_coverage_cache)
    if not Path(cache_filename).exists():
        raise CacheNotFoundError("Cache does not exist: %s", cache_filename)


def create_empty_partial_cache(partial_cache_filename, cache_backend):
    """Create an empty cache with temporary name to denote cache is being processed.

    Supported backends include zarray and memmap.

    Parameters
    ----------
    partial_cache_filename : str
        Full path to temporary/partial cache
    cache_backend : str
        Backend format of cache
    """
    LOG.debug("Creating %s", partial_cache_filename)
    if cache_backend == "zarr":
        # Zarrray data store is a directory
        Path(partial_cache_filename).mkdir(parents=True, exist_ok=True)
    else:
        Path(partial_cache_filename).touch(exist_ok=True)


def rename_partial_cache(partial_cache_filename, final_cache_filename):
    """Rename partial cache to final cache file name.

    Parameters
    ----------
    partial_cache_filename : str
        Full path to temporary/partial cache
    final_cache_filename : str
        Full path to complete cache
    """
    LOG.info("Renaming %s as %s", partial_cache_filename, final_cache_filename)
    Path(partial_cache_filename).rename(Path(final_cache_filename))


def get_geolocation(
    dt,
    gmd,
    fldk_lats,
    fldk_lons,
    BADVALS,
    area_def=None,
    resolution=None,
    geolocation_cache_backend="memmap",
    chunk_size=None,
    cache_solar_angles=False,
    scan_datetime=None,
    resource_tracker=None,
    cache_timeout_seconds=30,
):
    """
    Gather and return the geolocation data for the input metadata.

    Input metadata should be the metadata for a single ABI data file.

    If latitude/longitude have not been calculated with the metadata form the
    input data file they will be recalculated and stored for future use.
    They shouldn't change often. This will be slow the first time it is called
    after a metadata update, but fast thereafter.

    The same is true for satellite zenith and azimuth angles.

    Solar zenith ang azimuth angles are always calculated on the fly.
    This is because they actually change.
    This may be slow for full-disk images.
    """
    check_geolocation_cache_backend(geolocation_cache_backend)
    adname = "None"
    if area_def:
        adname = area_def.area_id

    if resolution:
        adname += f"_{resolution}"

    if resource_tracker is not None:
        key = f"GETGEO: {adname}".replace("None", "ALL")
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    try:
        fldk_sat_zen, fldk_sat_azm = get_satellite_angles(
            gmd,
            fldk_lats,
            fldk_lons,
            BADVALS,
            area_def,
            geolocation_cache_backend=geolocation_cache_backend,
            chunk_size=chunk_size,
            resource_tracker=resource_tracker,
            cache_timeout_seconds=cache_timeout_seconds,
        )
    except AutoGenError:
        return False

    # Determine which indicies will be needed for the input sector if there is one.
    if area_def is not None:
        try:
            lines, samples = get_indexes(
                gmd,
                fldk_lats,
                fldk_lons,
                area_def,
                geolocation_cache_backend=geolocation_cache_backend,
                chunk_size=chunk_size,
                resource_tracker=resource_tracker,
                cache_timeout_seconds=cache_timeout_seconds,
            )
        except AutoGenError:
            return False

        # Get lats, lons, and satellite zenith and azimuth angles for the required
        # points. This may not be entirely appropriate, especially if we want to do
        # something better than nearest neighbor interpolation.
        shape = area_def.shape

        # I'm not entirely sure why this happens from time to time, but sometimes the
        # lines/samples are the correct size, but not the correct shape. I should really
        # figure out the reason for this issue, but it's not entirely clear so in the
        # mean time reshape here as needed.
        if len(lines.shape) == 1 and lines.size == shape[0] * shape[1]:
            LOG.warning("Reshaping lines and samples - should not have to do this...")
            lines = np.reshape(lines, shape)
            samples = np.reshape(samples, shape)

        index_mask = lines != -999

        lons = np.full(shape, -999.1)
        lats = np.full(shape, -999.1)
        sat_zen = np.full(shape, -999.1)
        sat_azm = np.full(shape, -999.1)

        try:
            LOG.info("GETGEO Pulling lons from inds for %s", adname)
            lons[index_mask] = fldk_lons[lines[index_mask], samples[index_mask]]
            LOG.info("GETGEO Pulling lats from inds for %s", adname)
            lats[index_mask] = fldk_lats[lines[index_mask], samples[index_mask]]
            LOG.info("GETGEO Pulling sat_zen from inds for %s", adname)
            sat_zen[index_mask] = fldk_sat_zen[lines[index_mask], samples[index_mask]]
            LOG.info("GETGEO Pulling sat_azm from inds for %s", adname)
            sat_azm[index_mask] = fldk_sat_azm[lines[index_mask], samples[index_mask]]
        except IndexError as resp:
            raise CachedGeolocationIndexError(resp)

    else:
        lats = fldk_lats
        lons = fldk_lons
        sat_zen = fldk_sat_zen
        sat_azm = fldk_sat_azm

    # Get generator for solar zenith and azimuth angles
    LOG.info("GETGEO Must calculate solar zen/azm for sector %s", adname)
    sun_zen, sun_azm = calculate_solar_angles(
        gmd,
        lats,
        lons,
        dt,
        resource_tracker=resource_tracker,
        area_def=area_def,
        geolocation_cache_backend=geolocation_cache_backend,
        chunk_size=chunk_size,
        cache_solar_angles=cache_solar_angles,
        scan_datetime=scan_datetime,
        cache_timeout_seconds=cache_timeout_seconds,
    )
    LOG.info("GETGEO Done calculating solar zen/azm for sector %s", adname)

    # Satellite zenith angle masks are set appropriately for off-disk
    sat_zen = np.ma.masked_less_equal(sat_zen, -999.1)
    sat_azm = np.ma.masked_less_equal(sat_azm, -999.1)

    # Ensure sun_zen and sun_azm are masked appropriately for off-disk values.
    sun_zen = np.ma.masked_where(sat_zen.mask == True, sun_zen)
    sun_azm = np.ma.masked_where(sat_zen.mask == True, sun_azm)

    if resource_tracker is not None:
        resource_tracker.track_resource_usage(
            key=key, checkpoint=True, increment_key=True
        )

    if area_def is not None:
        # area_def.get_lonlats does NOT include any off disk masking.
        lons, lats = area_def.get_lonlats()
        # Set the lats and lons mask to sat_zen, which was set appropriately above.
        lats = np.ma.masked_where(sat_zen.mask == True, lats)
        lons = np.ma.masked_where(sat_zen.mask == True, lons)

    # Make into a dict
    # All the off-disk masking was set above, just catch any straggler -999 values.
    geolocation = {
        "latitude": np.ma.masked_less_equal(lats, -999.1),
        "longitude": np.ma.masked_less_equal(lons, -999.1),
        "satellite_zenith_angle": np.ma.masked_less_equal(sat_zen, -999.1),
        "satellite_azimuth_angle": np.ma.masked_less_equal(sat_azm, -999.1),
        "solar_zenith_angle": np.ma.masked_less_equal(sun_zen, -999.1),
        "solar_azimuth_angle": np.ma.masked_less_equal(sun_azm, -999.1),
    }
    if resource_tracker is not None:
        resource_tracker.track_resource_usage(
            key=key, checkpoint=True, increment_key=True
        )

    try:
        geolocation["Lines"] = np.array(lines)
        geolocation["Samples"] = np.array(samples)
    except NameError:
        pass

    if resource_tracker is not None:
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    return geolocation


def get_satellite_angles(
    metadata,
    lats,
    lons,
    BADVALS,
    sect=None,
    geolocation_cache_backend="memmap",
    chunk_size=None,
    resource_tracker=None,
    cache_timeout_seconds=30,
):
    """Get satellite angles."""
    # If the filename format needs to change for the pre-generated geolocation
    # files, please discuss prior to changing.  It will force recreation of all
    # files, which can be problematic for large numbers of sectors
    check_geolocation_cache_backend(geolocation_cache_backend)
    fname = get_geolocation_cache_filename(
        "GEOSAT",
        metadata,
        geolocation_cache_backend=geolocation_cache_backend,
        chunk_size=chunk_size,
    )
    fname_partial = fname + ".partial"

    if resource_tracker is not None:
        key = "GEO SAT ANGLES: " + str(Path(fname).name)
        if sect:
            key += f"_{sect.area_id}"
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    if not Path(fname).exists() and not Path(fname_partial).exists():
        # First touch a file with the partial cache name to identify we're creating the
        # cache.
        create_empty_partial_cache(fname_partial, geolocation_cache_backend)
        if sect is not None and DONT_AUTOGEN_GEOLOCATION and "tc2019" not in sect.name:
            msg = (
                "GETGEO Requested NO AUTOGEN GEOLOCATION. "
                + "Could not create sat_file for ad {}: {}"
            ).format(metadata["scene"], fname)
            LOG.error(msg)
            raise AutoGenError(msg)

        LOG.info("Calculating satellite zenith and azimuth angles.")
        pi = np.pi
        deg2rad = pi / 180.0  # NOQA
        rad2deg = 180.0 / pi  # NOQA
        sub_lat = 0.0  # NOQA
        sub_lon = metadata["lon0"]  # NOQA
        alt = metadata["H_m"] / 1000.0  # NOQA
        num_lines = metadata["num_lines"]  # NOQA
        num_samples = metadata["num_samples"]  # NOQA

        # Convert lats / lons to radians from sub point
        LOG.debug("Calculating beta")
        # fmt: off
        beta = ne.evaluate("arccos(cos(deg2rad * (lats - sub_lat)) * cos(deg2rad * (lons - sub_lon)))")  # NOQA
        # fmt: on
        bad = lats == BADVALS["Off_Of_Disk"]
        if resource_tracker is not None:
            resource_tracker.track_resource_usage(
                key=key, checkpoint=True, increment_key=True
            )

        # Calculate satellite zenith angle
        LOG.debug("Calculating satellite zenith angle")
        zen = ne.evaluate("alt * sin(beta) / sqrt(1.808e9 - 5.3725e8 * cos(beta))")
        # Where statements take the place of np.clip(zen, - 1.0, 1.0)
        ne.evaluate(
            "rad2deg * arcsin(where(zen < -1.0, -1.0, where(zen > 1.0, 1.0, zen)))",
            out=zen,
        )
        zen[bad] = BADVALS["Off_Of_Disk"]
        if resource_tracker is not None:
            resource_tracker.track_resource_usage(
                key=key, checkpoint=True, increment_key=True
            )

        # Sat azimuth
        LOG.debug("Calculating satellite azimuth angle")
        azm = ne.evaluate("sin(deg2rad * (lons - sub_lon)) / sin(beta)")
        ne.evaluate(
            "rad2deg * arcsin(where(azm < -1.0, -1.0, where(azm > 1.0, 1.0, azm)))",
            out=azm,
        )
        ne.evaluate("where(lats < sub_lat, 180.0 - azm, azm)", out=azm)
        ne.evaluate("where(azm < 0.0, 360.0 + azm, azm)", out=azm)
        azm[bad] = BADVALS["Off_Of_Disk"]
        if resource_tracker is not None:
            resource_tracker.track_resource_usage(
                key=key, checkpoint=True, increment_key=True
            )

        LOG.info("Done calculating satellite zenith and azimuth angles")

        if geolocation_cache_backend == "memmap":
            LOG.info("Storing to %s", fname)
            with open(fname_partial, "w") as df:
                zen.tofile(df)
                azm.tofile(df)
        elif geolocation_cache_backend == "zarr":
            if chunk_size:
                chunks = (chunk_size, chunk_size)
            else:
                chunks = None

            LOG.info("Storing sat zen/azm to %s (chunks=%s)", fname, chunks)
            # NOTE zarr does NOT have a close method, so you can NOT use with context.
            zf = zarr.open(fname_partial, mode="w")
            # Assume azm and zen shape and dtype are the same
            kwargs = {
                "shape": azm.shape,
                "dtype": azm.dtype,
            }
            # As of Python 3.11, can't pass chunks=None into create_dataset
            if chunks:
                # Chunks must be a tuple of the same shape as array.
                kwargs["chunks"] = tuple([chunk_size] * azm.ndim)
            zf.create_dataset("azm", **kwargs)
            zf.create_dataset("zen", **kwargs)
            zf["azm"][:] = azm
            zf["zen"][:] = zen
        rename_partial_cache(fname_partial, fname)

        # Possible switch to xarray based geolocation files, but we lose memmapping.
        # ds = xarray.Dataset({'zeniths':(['x','y'],zen),'azimuths':(['x','y'],azm)})
        # ds.to_netcdf(fname)
    else:
        check_for_partial_cache(fname, fname_partial, cache_timeout_seconds)
        if geolocation_cache_backend == "memmap":
            # Create a memmap to the lat/lon file
            # Nothing will be read until explicitly requested
            # We are mapping this here so that the lats and lons are available when
            # calculating satlelite angles
            LOG.info(
                "GETGEO memmap to {} : lat/lon file for {}".format(
                    fname, metadata["scene"]
                )
            )

            shape = (metadata["num_lines"], metadata["num_samples"])
            offset = 8 * metadata["num_samples"] * metadata["num_lines"]
            zen = np.memmap(fname, mode="r", dtype=np.float64, offset=0, shape=shape)
            if resource_tracker is not None:
                resource_tracker.track_resource_usage(
                    key=key, checkpoint=True, increment_key=True
                )
            azm = np.memmap(
                fname, mode="r", dtype=np.float64, offset=offset, shape=shape
            )
            if resource_tracker is not None:
                resource_tracker.track_resource_usage(
                    key=key, checkpoint=True, increment_key=True
                )
            # Possible switch to xarray based geolocation files, but we lose memmapping.
            # saved_xarray = xarray.load_dataset(fname)
            # zen = saved_xarray['zeniths'].to_masked_array()
            # azm = saved_xarray['azimuths'].to_masked_array()
        elif geolocation_cache_backend == "zarr":
            LOG.info(
                "GETGEO zarr to {} : azm/zen file for {}".format(
                    fname, metadata["scene"]
                )
            )
            shape = (metadata["num_lines"], metadata["num_samples"])
            # chunk_x, chunk_y = [int(x/100) for x in lats.shape]
            # NOTE zarr does NOT have a close method, so you can NOT use with context.
            zf = zarr.open(fname, mode="r")
            azm = zf["azm"]
            zen = zf["zen"]

    if resource_tracker is not None:
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    return zen, azm


def get_indexes(
    metadata,
    lats,
    lons,
    area_def,
    geolocation_cache_backend="memmap",
    chunk_size=None,
    resource_tracker=None,
    cache_timeout_seconds=30,
):
    """
    Return two 2-D arrays containing the X and Y indexes.

    These are indices that should be used from the raw data for the input
    sector definition.
    """
    # The get_neighbor_info function returns three four arrays:
    #    valid_input_index: a 1D boolean array indicating where the source lats and lons
    #                       are valid values (not masked)
    #    valid_output_index: a 1D boolean array indicating where the sector lats and
    #                        lons are valid values (always true everywhere)
    #    index_array: a 1D array of ints indicating which indicies in the flattened
    #                 inputs should be used to fit the sector lats and lons
    #    distance_array: Distances from the source point for each found point.
    #
    # What we do here is feed our data lats/lons to get_neighbour_info.
    # We then reshape valid_input_index to fit our lats/lons and find the 2D indicies
    #   where the input lats and lons were good.
    # We then subset the "good" indicies with index_array to retrieve the required
    #   indicies for the sector.
    # This is complicated because get_neighbour_info does not report the indicies of the
    #   input data, but instead reports the indicies of the flattened data where
    #   valid_input_index is True

    # Get filename for sector indicies

    # If the filename format needs to change for the pre-generated geolocation
    # files, please discuss prior to changing.  It will force recreation of all
    # files, which can be problematic for large numbers of sectors
    check_geolocation_cache_backend(geolocation_cache_backend)
    fname = get_geolocation_cache_filename(
        "GEOINDS",
        metadata,
        area_def,
        geolocation_cache_backend=geolocation_cache_backend,
        chunk_size=None,
    )
    fname_partial = fname + ".partial"
    if Path(fname_partial.replace("partial", "no_coverage")).exists():
        msg = "NO GOOD DATA AVAILABLE, can not read geostationary dataset"
        LOG.info(msg)
        raise CoverageError(msg)

    if resource_tracker is not None:
        key = "GEOINDS: " + str(Path(fname).name)
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    if not Path(fname).exists() and not Path(fname_partial).exists():
        # First touch a file with the partial cache name to identify we're creating the
        # cache.
        create_empty_partial_cache(fname_partial, geolocation_cache_backend)
        if (
            area_def is not None
            and DONT_AUTOGEN_GEOLOCATION
            and "tc2019" not in area_def.area_id
        ):
            msg = (
                "GETGEO Requested NO AUTOGEN GEOLOCATION. "
                + "Could not create inds_file {} for {}"
            ).format(fname, area_def.area_id)
            LOG.error(msg)
            raise AutoGenError(msg)

        # Allocate the full disk area definition
        LOG.info("    GETGEOINDS Masking longitudes")
        lons = np.ma.masked_less(lons, -999.1)
        LOG.info("    GETGEOINDS Wrapping longitudes, pyresample expects -180 to 180")
        # NOTE: it appears pyresample wrap_longitudes can sometimes return a
        # different dtype than passed in. SwathDefinition will fail if dtype
        # does not match between lats and lons. I believe pyresample
        # wrap_longitudes began returning different dtype after numpy 2.0
        # upgrade. It is probably a bug with pyresample, but this will ensure
        # it does not break our processing.
        lons = utils.wrap_longitudes(lons).astype(lats.dtype)
        LOG.info(
            "    GETGEOINDS Creating full disk swath definition for {}".format(
                area_def.area_id
            )
        )
        fldk_ad = SwathDefinition(
            np.ma.masked_less(lons, -999.1), np.ma.masked_less(lats, -999.1)
        )
        ad = area_def

        # Radius of influence will be 10 times the nominal spatial resolution of the
        #   data in meters
        # This uses the only piece of information available concerning resolution
        # in the metadata
        LOG.info(
            "    GETGEOINDS Calculating radius of influence {}".format(area_def.area_id)
        )
        if "res_km" not in metadata.keys():
            shape = lons.shape
            latres = (
                np.abs(
                    lats[int(shape[0] / 2), int(shape[1] / 2)]
                    - lats[int(shape[0] / 2 + 1), int(shape[1] / 2)]
                )
                * 111.1
                * 1000
            )
            lonres = (
                np.abs(
                    lons[int(shape[0] / 2), int(shape[1] / 2)]
                    - lons[int(shape[0] / 2), int(shape[1] / 2 + 1)]
                )
                * 111.1
                * 1000
            )
            # Use larger of the two values times 10 as ROI for interpolation
            # Would be nice to use something more dynamic to save CPU time here
            # Kind of stuck as long as we use pyresample
            metadata["res_km"] = max(latres, lonres) / 1000.0
        roi = (
            metadata["roi_factor"] * 1000.0 * metadata["res_km"]
        )  # roi_factor * resolution in meters
        LOG.info(
            "    GETGEOINDS Running get_neighbour_info %s roi %s res_km %s "
            "roi_factor %s",
            area_def.area_id,
            roi,
            metadata["res_km"],
            metadata["roi_factor"],
        )
        (
            valid_input_index,
            valid_output_index,
            index_array,
            distance_array,
        ) = get_neighbour_info(
            fldk_ad, ad, radius_of_influence=roi, neighbours=1, nprocs=nprocs
        )
        LOG.info(
            "    GETGEOINDS Getting good lines and samples {}".format(area_def.area_id)
        )
        good_lines, good_samples = np.where(valid_input_index.reshape(lats.shape))
        if len(good_lines) == 0 and len(good_samples) == 0:
            # Rename the partial cache and flag as no coverage if it exists.
            if Path(fname_partial).exists():
                rename_partial_cache(
                    fname_partial, fname_partial.replace("partial", "no_coverage")
                )
            raise CoverageError(
                "NO GOOD DATA AVAILABLE, can not read geostationary dataset"
            )
        LOG.info(
            "    GETGEOINDS Reshaping lines and samples {}".format(area_def.area_id)
        )
        # When get_neighbour_info does not find a good value for a specific location it
        #   fills index_array with the maximum index + 1.  So, just throw away all of
        #   the out of range indexes.
        index_mask = index_array == len(good_lines)
        # good_index_array = index_array[np.where(index_array != len(good_lines))]
        lines = np.empty(ad.size, dtype=np.int64)
        lines[index_mask] = -999.1
        lines[~index_mask] = good_lines[index_array[~index_mask]]
        samples = np.empty(ad.size, dtype=np.int64)
        samples[index_mask] = -999.1
        samples[~index_mask] = good_samples[index_array[~index_mask]]

        LOG.info(
            "    GETGEOINDS Writing to {} : inds_file for {}".format(
                fname, area_def.area_id
            )
        )
        if geolocation_cache_backend == "memmap":
            # Store indicies for sector
            with open(str(fname_partial), "w") as df:
                lines.tofile(df)
                samples.tofile(df)
            # Store indicies for sector
            # Possible switch to xarray based geolocation files, but we lose memmapping.
            # ds = xarray.Dataset({'lines':(['x'],lines),'samples':(['x'],samples)})
            # ds.to_netcdf(fname_partial)
        elif geolocation_cache_backend == "zarr":
            if chunk_size:
                chunks = (chunk_size, chunk_size)
            else:
                chunks = None

            LOG.info("Storing lines/samples to %s (chunks=%s)", fname, chunks)
            # NOTE zarr does NOT have a close method, so you can NOT use with context.
            zf = zarr.open(fname_partial, mode="w")
            # Assume both arrays have the same shape and dtype
            kwargs = {
                "shape": lines.shape,
                "dtype": lines.dtype,
            }
            # As of Python 3.11, can't pass chunks=None into create_dataset
            if chunks:
                # Chunks must be a tuple of the same shape as array.
                kwargs["chunks"] = tuple([chunk_size] * lines.ndim)
            zf.create_dataset("lines", **kwargs)
            zf.create_dataset("samples", **kwargs)
            zf["lines"][:] = lines
            zf["samples"][:] = samples
        rename_partial_cache(fname_partial, fname)

    else:
        check_for_partial_cache(fname, fname_partial, cache_timeout_seconds)
        LOG.info(
            "GETGEO to %s : inds file for %s, roi_factor %s",
            fname,
            metadata["scene"],
            metadata["roi_factor"],
        )
        LOG.info(
            "GETGEO to %s : lat/lon file for %s, roi_factor %s",
            fname,
            metadata["scene"],
            metadata["roi_factor"],
        )
        shape = area_def.shape
        try:
            if geolocation_cache_backend == "memmap":
                # Create a memmap to the lat/lon file
                # Nothing will be read until explicitly requested
                # We are mapping this here so that the lats and lons are available when
                # calculating satlelite angles.
                # LOG.info(
                #   'GETGEO memmap to %s : inds file for %s, roi_factor %s, res_km %s',
                #   fname,
                #   metadata['scene'],
                #   metadata['roi_factor'],
                #   metadata['res_km']
                # )
                # LOG.info(
                #   'GETGEO memmap to %s : %s file for %s, roi_factor %s, res_km %s',
                #    fname,
                #   "lat/lon",
                #   metadata['scene'],
                #   metadata['roi_factor'],
                #   metadata['res_km']
                # )
                offset = 8 * shape[0] * shape[1]
                LOG.info(
                    "GETGEO memmap from %s : lines for %s, shape %s",
                    fname,
                    metadata["scene"],
                    shape,
                )
                lines = np.memmap(
                    fname, mode="r", dtype=np.int64, offset=0, shape=shape
                )
                LOG.info(
                    "GETGEO memmap from %s : samples for %s, offset %s",
                    fname,
                    metadata["scene"],
                    offset,
                )
                samples = np.memmap(
                    fname, mode="r", dtype=np.int64, offset=offset, shape=shape
                )
            elif geolocation_cache_backend == "zarr":
                # Load lines/samples from pre-calculated zarr
                LOG.info(
                    "GETGEO zarr to {} : inds file for {}".format(
                        fname, area_def.area_id
                    )
                )
                # NOTE zarr does NOT have close method, so you can NOT use with context.
                zf = zarr.open(fname, mode="r")
                if "lines" not in zf or "samples" not in zf:
                    LOG.exception(
                        "lines and samples not in zarr directory, corrupt zarr? "
                        f"Please remove {fname} and re-run this script."
                    )
                    raise RuntimeError(
                        "lines and samples not in zarr directory, corrupt zarr? "
                        f"Please remove the directory:\n"
                        f"{fname}\n"
                        "and re-run this script."
                    )
                lines = zf["lines"]
                samples = zf["samples"]
                lines = np.reshape(lines, shape=shape)
                samples = np.reshape(samples, shape=shape)
        except ValueError as resp:
            LOG.warning(
                "Mismatched geolocation file size (Empty?  No coverage?  Or old "
                "sector of different shape?"
            )
            raise CachedGeolocationIndexError(resp)

    if resource_tracker is not None:
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    # Possible switch to xarray based geolocation files, but we lose memmapping.
    # saved_xarray = xarray.load_dataset(fname)
    # lines= saved_xarray['lines'].to_masked_array()
    # samples = saved_xarray['samples'].to_masked_array()
    return lines, samples


def calculate_solar_angles(
    metadata,
    lats,
    lons,
    dt,
    resource_tracker=None,
    area_def=None,
    geolocation_cache_backend=None,
    chunk_size=None,
    cache_solar_angles=False,
    scan_datetime=None,
    cache_timeout_seconds=30,
):
    """Calculate solar angles."""
    # If debug is set to True, memory savings will be turned off in order to keep
    # all calculated results for inspection.
    # If set to False, variables will attempt to reuse memory when possible which
    # will result in some results being overwritten when no longer needed.
    debug = False
    if area_def:
        adname = area_def.area_id
    else:
        adname = "None"
    if cache_solar_angles:
        check_geolocation_cache_backend(geolocation_cache_backend)
        prefix = "GEOSOL"
        if scan_datetime is not None:
            prefix += f"_{scan_datetime.strftime('%Y%m%dT%H%M%S.%fZ')}"
        fname = get_geolocation_cache_filename(
            prefix,
            metadata,
            area_def=area_def,
            geolocation_cache_backend=geolocation_cache_backend,
            chunk_size=chunk_size,
            solar_angles=True,
        )
        fname_partial = fname + ".partial"
        cache_exists = Path(fname).exists()
    else:
        cache_exists = False

    LOG.info("Calculating solar zenith and azimuth angles.")

    if resource_tracker is not None:
        key = f"GEO SOLAR ANGLES: {adname}_{lats.shape[0]}x{lats.shape[1]}".replace(
            "None", "ALL"
        )
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    # Getting good value mask
    # good = lats > -999
    # good_lats = lats[good]
    # good_lons = lons[good]
    if cache_solar_angles is False or (cache_solar_angles and cache_exists is False):
        if cache_solar_angles and not cache_exists and not Path(fname_partial).exists():
            # First touch a file with the partial cache name to identify we're creating
            # the cache.
            create_empty_partial_cache(fname_partial, geolocation_cache_backend)
        # Constants
        pi = np.pi
        pi2 = 2 * pi  # NOQA
        num_lines = metadata["num_lines"]
        num_samples = metadata["num_samples"]
        shape = (num_lines, num_samples)  # NOQA
        size = num_lines * num_samples  # NOQA
        deg2rad = pi / 180.0  # NOQA
        rad2deg = 180.0 / pi  # NOQA

        # Calculate any non-data dependent quantities
        jday = float(dt.strftime("%j"))
        a1 = (1.00554 * jday - 6.28306) * (pi / 180.0)
        a2 = (1.93946 * jday - 23.35089) * (pi / 180.0)
        et = -7.67825 * np.sin(a1) - 10.09176 * np.sin(a2)  # NOQA

        # Solar declination radians
        LOG.debug("Calculating delta")
        delta = deg2rad * 23.4856 * np.sin(np.deg2rad(0.9683 * jday - 78.00878))  # NOQA

        # Pre-generate sin and cos of latitude
        LOG.debug("Calculating sin and cos")
        sin_lat = ne.evaluate("sin(deg2rad * lats)")  # NOQA
        cos_lat = ne.evaluate("cos(deg2rad * lats)")  # NOQA

        # Hour angle
        LOG.debug("Initializing hour angle")
        solar_time = dt.hour + dt.minute / 60.0 + dt.second / 3600.0  # NOQA
        h_ang = ne.evaluate(
            "deg2rad * ((solar_time + lons / 15.0 + et / 60.0 - 12.0) * 15.0)"
        )

        # Pre-allocate all required arrays
        # This avoids having to allocate them again every time the generator is accessed
        LOG.debug("Allocating arrays")
        sun_elev = np.empty_like(h_ang)

        # Hour angle at all points in radians
        LOG.debug("Calculating hour angle")

        # Sun elevation
        LOG.debug("Calculating sun elevation angle using sin and cos")
        ne.evaluate(
            "arcsin(sin_lat * sin(delta) + cos_lat * cos(delta) * cos(h_ang))",
            out=sun_elev,
        )  # NOQA

        LOG.debug("Calculating caz")
        # No longer need sin_lat and this saves 3.7GB
        if not debug:
            caz = sin_lat
        else:
            caz = np.empty_like(sin_lat)
        ne.evaluate(
            "-cos_lat * sin(delta) + sin_lat * cos(delta) * cos(h_ang) / cos(sun_elev)",
            out=caz,
        )  # NOQA

        LOG.debug("Calculating az")
        # No longer need h_ang and this saves 3.7GB
        if not debug:
            az = h_ang
        else:
            az = np.empty_like(h_ang)
        ne.evaluate("cos(delta) * sin(h_ang) / cos(sun_elev)", out=az)  # NOQA
        # No longer need sin_lat and this saves 3.7GB
        if not debug:
            sun_azm = cos_lat
        else:
            sun_azm = np.empty_like(cos_lat)
        ne.evaluate(
            "where(az <= -1, -pi / 2.0, where(az > 1, pi / 2.0, arcsin(az)))",
            out=sun_azm,
        )

        LOG.debug("Calculating solar zenith angle")
        # No longer need sun_elev and this saves 3.7GB RAM
        if not debug:
            sun_zen = sun_elev
        else:
            sun_zen = np.empty_like(sun_elev)
        ne.evaluate("90.0 - rad2deg * sun_elev", out=sun_zen)

        LOG.debug("Calculating solar azimuth angle")
        ne.evaluate(
            "where(caz <= 0, pi - sun_azm,where(az <= 0, 2.0 * pi + sun_azm, sun_azm))",
            out=sun_azm,
        )
        sun_azm += pi
        ne.evaluate(
            "where(sun_azm > 2.0 * pi, sun_azm - 2.0 * pi, sun_azm)", out=sun_azm
        )
        # ne.evaluate('where(caz <= 0, pi - sun_azm, sun_azm) + pi', out=sun_azm)
        # ne.evaluate('rad2deg * where(sun_azm < 0, sun_azm + pi2, where(sun_azm >= pi2,
        #                                                     sun_azm - pi2, sun_azm))',
        #                                                                  out=sun_azm)
        if cache_solar_angles:
            if geolocation_cache_backend == "memmap":
                LOG.info("Storing to %s", fname_partial)
                with open(fname_partial, "w") as df:
                    sun_zen.tofile(df)
                    sun_azm.tofile(df)
            elif geolocation_cache_backend == "zarr":
                if chunk_size:
                    chunks = (chunk_size, chunk_size)
                else:
                    chunks = None

                LOG.info("Storing solar angles to %s (chunks=%s)", fname, chunks)
                # NOTE zarr does NOT have close method, so you can NOT use the context.
                zf = zarr.open(fname_partial, mode="w")
                # Assume both arrays have the same shape and dtype
                kwargs = {
                    "shape": sun_azm.shape,
                    "dtype": sun_azm.dtype,
                }
                # As of Python 3.11, can't pass chunks=None into create_dataset
                if chunks:
                    # Chunks must be a tuple of the same shape as array.
                    kwargs["chunks"] = tuple([chunk_size] * sun_azm.ndim)
                zf.create_dataset("sun_azm", **kwargs)
                zf.create_dataset("sun_zen", **kwargs)
                zf["sun_azm"][:] = sun_azm
                zf["sun_zen"][:] = sun_zen
            rename_partial_cache(fname_partial, fname)

        LOG.info("Done calculating solar zenith and azimuth angles")
    else:
        check_for_partial_cache(fname, fname_partial, cache_timeout_seconds)
        if geolocation_cache_backend == "memmap":
            # Create a memmap to the lat/lon file
            # Nothing will be read until explicitly requested
            # We are mapping this here so that the lats and lons are available when
            # calculating satlelite angles
            LOG.info(
                "GETGEO memmap to {} : lat/lon file for {}".format(
                    fname, metadata["scene"]
                )
            )

            shape = (metadata["num_lines"], metadata["num_samples"])
            offset = 8 * metadata["num_samples"] * metadata["num_lines"]
            sun_zen = np.memmap(
                fname, mode="r", dtype=np.float64, offset=0, shape=shape
            )
            if resource_tracker is not None:
                resource_tracker.track_resource_usage(
                    key=key, checkpoint=True, increment_key=True
                )
            sun_azm = np.memmap(
                fname, mode="r", dtype=np.float64, offset=offset, shape=shape
            )
            if resource_tracker is not None:
                resource_tracker.track_resource_usage(
                    key=key, checkpoint=True, increment_key=True
                )
            # Possible switch to xarray based geolocation files, but we lose memmapping.
            # saved_xarray = xarray.load_dataset(fname)
            # zen = saved_xarray['zeniths'].to_masked_array()
            # azm = saved_xarray['azimuths'].to_masked_array()
        elif geolocation_cache_backend == "zarr":
            LOG.info(
                "GETGEO zarr to {} : sun_azm/sun_zen file for {}".format(
                    fname, metadata["scene"]
                )
            )
            shape = (metadata["num_lines"], metadata["num_samples"])
            # chunk_x, chunk_y = [int(x/100) for x in lats.shape]
            # NOTE zarr does NOT have a close method, so you can NOT use with context.
            zf = zarr.open(fname, mode="r")
            sun_azm = zf["sun_azm"]
            sun_zen = zf["sun_zen"]

    if resource_tracker is not None:
        resource_tracker.track_resource_usage(
            logstr="MEMUSG", verbose=False, key=key, increment_key=True
        )

    return sun_zen, sun_azm
