# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Generalized geolocation calculations for geostationary satellites."""

import os
import logging
import numpy as np
from pyresample import utils
from pyresample.geometry import SwathDefinition
from pyresample.kd_tree import get_neighbour_info  # , get_sample_from_neighbour_info

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

DONT_AUTOGEN_GEOLOCATION = False
if os.getenv("DONT_AUTOGEN_GEOLOCATION"):
    DONT_AUTOGEN_GEOLOCATION = True
GEOLOCDIR = os.path.join(gpaths["GEOIPS_OUTDIRS"], "longterm_files", "geolocation")

# default dynamic geoloc dir for NRL
DYNAMIC_GEOLOCDIR = os.path.join(
    gpaths["GEOIPS_OUTDIRS"], "longterm_files", "geolocation_dynamic"
)

READ_GEOLOCDIRS = []
if os.getenv("READ_GEOLOCDIRS"):
    READ_GEOLOCDIRS = os.getenv("READ_GEOLOCDIRS").split(":")


class AutoGenError(Exception):
    """Raise exception on auto generated geolocation error."""

    pass


def get_geolocation_cache_filename(pref, metadata, area_def=None):
    """Set the location and filename format for the cached geolocation files.

    There is a separate filename format for satellite latlons and sector latlons

    Notes
    -----
    Changing geolocation filename format will force recreation of all
    files, which can be problematic for large numbers of sectors.
    """
    cache = os.path.join(GEOLOCDIR, metadata["platform_name"])
    from geoips.sector_utils.utils import is_dynamic_sector

    if is_dynamic_sector(area_def):
        cache = os.path.join(DYNAMIC_GEOLOCDIR, metadata["platform_name"])
    if not os.path.isdir(cache):
        try:
            os.makedirs(cache)
        except FileExistsError:
            pass

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

    fname += ".dat"

    # Check alternative read-only directories (i.e. operational)
    for dirname in READ_GEOLOCDIRS:
        if os.path.exists(os.path.join(dirname, metadata["platform_name"], fname)):
            return os.path.join(dirname, metadata["platform_name"], fname)

    # If not found, return the normal cached filename
    return os.path.join(cache, fname)


def get_geolocation(dt, gmd, fldk_lats, fldk_lons, BADVALS, area_def=None):
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
    adname = "None"
    if area_def:
        adname = area_def.area_id

    try:
        fldk_sat_zen, fldk_sat_azm = get_satellite_angles(
            gmd, fldk_lats, fldk_lons, BADVALS, area_def
        )
    except AutoGenError:
        return False

    # Determine which indicies will be needed for the input sector if there is one.
    if area_def is not None:
        try:
            lines, samples = get_indexes(gmd, fldk_lats, fldk_lons, area_def)
        except AutoGenError:
            return False

        # Get lats, lons, and satellite zenith and azimuth angles for the required
        # points. This may not be entirely appropriate, especially if we want to do
        # something better than nearest neighbor interpolation.
        shape = area_def.shape
        index_mask = lines != -999

        lons = np.full(shape, -999.1)
        lats = np.full(shape, -999.1)
        sat_zen = np.full(shape, -999.1)
        sat_azm = np.full(shape, -999.1)

        LOG.info("GETGEO Pulling lons from inds for %s", adname)
        lons[index_mask] = fldk_lons[lines[index_mask], samples[index_mask]]
        LOG.info("GETGEO Pulling lats from inds for %s", adname)
        lats[index_mask] = fldk_lats[lines[index_mask], samples[index_mask]]
        LOG.info("GETGEO Pulling sat_zen from inds for %s", adname)
        sat_zen[index_mask] = fldk_sat_zen[lines[index_mask], samples[index_mask]]
        LOG.info("GETGEO Pulling sat_azm from inds for %s", adname)
        sat_azm[index_mask] = fldk_sat_azm[lines[index_mask], samples[index_mask]]

    else:
        lats = fldk_lats
        lons = fldk_lons
        sat_zen = fldk_sat_zen
        sat_azm = fldk_sat_azm

    # Get generator for solar zenith and azimuth angles
    LOG.info("GETGEO Must calculate solar zen/azm for sector %s", adname)
    sun_zen, sun_azm = calculate_solar_angles(gmd, lats, lons, dt)
    LOG.info("GETGEO Done calculating solar zen/azm for sector %s", adname)
    sun_zen = np.ma.masked_less_equal(sun_zen, -999.1)
    sun_azm = np.ma.masked_less_equal(sun_azm, -999.1)

    if area_def is not None:
        lons, lats = area_def.get_lonlats()

    # Make into a dict
    geolocation = {
        "latitude": np.ma.masked_less_equal(lats, -999.1),
        "longitude": np.ma.masked_less_equal(lons, -999.1),
        "satellite_zenith_angle": np.ma.masked_less_equal(sat_zen, -999.1),
        "satellite_azimuth_angle": np.ma.masked_less_equal(sat_azm, -999.1),
        "solar_zenith_angle": np.ma.masked_less_equal(sun_zen, -999.1),
        "solar_azimuth_angle": np.ma.masked_less_equal(sun_azm, -999.1),
    }

    try:
        geolocation["Lines"] = np.array(lines)
        geolocation["Samples"] = np.array(samples)
    except NameError:
        pass

    return geolocation


def get_satellite_angles(metadata, lats, lons, BADVALS, sect=None):
    """Get satellite angles."""
    # If the filename format needs to change for the pre-generated geolocation
    # files, please discuss prior to changing.  It will force recreation of all
    # files, which can be problematic for large numbers of sectors
    fname = get_geolocation_cache_filename("GEOSAT", metadata)
    if not os.path.isfile(fname):
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

        # Calculate satellite zenith angle
        LOG.debug("Calculating satellite zenith angle")
        zen = ne.evaluate("alt * sin(beta) / sqrt(1.808e9 - 5.3725e8 * cos(beta))")
        # Where statements take the place of np.clip(zen, - 1.0, 1.0)
        ne.evaluate(
            "rad2deg * arcsin(where(zen < -1.0, -1.0, where(zen > 1.0, 1.0, zen)))",
            out=zen,
        )
        zen[bad] = BADVALS["Off_Of_Disk"]

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

        LOG.info("Done calculating satellite zenith and azimuth angles")

        with open(fname, "w") as df:
            zen.tofile(df)
            azm.tofile(df)
        # Possible switch to xarray based geolocation files, but we lose memmapping.
        # ds = xarray.Dataset({'zeniths':(['x','y'],zen),'azimuths':(['x','y'],azm)})
        # ds.to_netcdf(fname)

    # Create a memmap to the lat/lon file
    # Nothing will be read until explicitly requested
    # We are mapping this here so that the lats and lons are available when
    # calculating satlelite angles
    LOG.info(
        "GETGEO memmap to {} : lat/lon file for {}".format(fname, metadata["scene"])
    )

    shape = (metadata["num_lines"], metadata["num_samples"])
    offset = 8 * metadata["num_samples"] * metadata["num_lines"]
    zen = np.memmap(fname, mode="r", dtype=np.float64, offset=0, shape=shape)
    azm = np.memmap(fname, mode="r", dtype=np.float64, offset=offset, shape=shape)
    # Possible switch to xarray based geolocation files, but we lose memmapping.
    # saved_xarray = xarray.load_dataset(fname)
    # zen = saved_xarray['zeniths'].to_masked_array()
    # azm = saved_xarray['azimuths'].to_masked_array()

    return zen, azm


def get_indexes(metadata, lats, lons, area_def):
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
    fname = get_geolocation_cache_filename("GEOINDS", metadata, area_def)

    if not os.path.isfile(fname):
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
        lons = utils.wrap_longitudes(lons)
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
        # Store indicies for sector
        with open(str(fname), "w") as df:
            lines.tofile(df)
            samples.tofile(df)
        # Store indicies for sector
        # Possible switch to xarray based geolocation files, but we lose memmapping.
        # ds = xarray.Dataset({'lines':(['x'],lines),'samples':(['x'],samples)})
        # ds.to_netcdf(fname)

    # Create a memmap to the lat/lon file
    # Nothing will be read until explicitly requested
    # We are mapping this here so that the lats and lons are available when calculating
    # satlelite angles.
    # LOG.info('GETGEO memmap to %s : inds file for %s, roi_factor %s, res_km %s',
    #          fname, metadata['scene'], metadata['roi_factor'], metadata['res_km'])
    # LOG.info('GETGEO memmap to %s : lat/lon file for %s, roi_factor %s, res_km %s',
    #          fname, metadata['scene'], metadata['roi_factor'], metadata['res_km'])
    LOG.info(
        "GETGEO memmap to %s : inds file for %s, roi_factor %s",
        fname,
        metadata["scene"],
        metadata["roi_factor"],
    )
    LOG.info(
        "GETGEO memmap to %s : lat/lon file for %s, roi_factor %s",
        fname,
        metadata["scene"],
        metadata["roi_factor"],
    )
    try:
        shape = area_def.shape
        offset = 8 * shape[0] * shape[1]
        LOG.info(
            "GETGEO memmap from %s : lines for %s, shape %s",
            fname,
            metadata["scene"],
            shape,
        )
        lines = np.memmap(fname, mode="r", dtype=np.int64, offset=0, shape=shape)
        LOG.info(
            "GETGEO memmap from %s : samples for %s, offset %s",
            fname,
            metadata["scene"],
            offset,
        )
        samples = np.memmap(fname, mode="r", dtype=np.int64, offset=offset, shape=shape)
    except ValueError as resp:
        LOG.warning(
            "Mismatched geolocation file size (Empty?  No coverage?  Or old sector of "
            "different shape?"
        )
        raise IndexError(resp)
    # Possible switch to xarray based geolocation files, but we lose memmapping.
    # saved_xarray = xarray.load_dataset(fname)
    # lines= saved_xarray['lines'].to_masked_array()
    # samples = saved_xarray['samples'].to_masked_array()
    return lines, samples


def calculate_solar_angles(metadata, lats, lons, dt):
    """Calculate solar angles."""
    # If debug is set to True, memory savings will be turned off in order to keep
    # all calculated results for inspection.
    # If set to False, variables will attempt to reuse memory when possible which
    # will result in some results being overwritten when no longer needed.
    debug = False

    LOG.info("Calculating solar zenith and azimuth angles.")

    # Getting good value mask
    # good = lats > -999
    # good_lats = lats[good]
    # good_lons = lons[good]

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
        "arcsin(sin_lat * sin(delta) + cos_lat * cos(delta) * cos(h_ang))", out=sun_elev
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
        "where(az <= -1, -pi / 2.0, where(az > 1, pi / 2.0, arcsin(az)))", out=sun_azm
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
        "where(caz <= 0, pi - sun_azm, where(az <= 0, 2.0 * pi + sun_azm, sun_azm))",
        out=sun_azm,
    )
    sun_azm += pi
    ne.evaluate("where(sun_azm > 2.0 * pi, sun_azm - 2.0 * pi, sun_azm)", out=sun_azm)
    # ne.evaluate('where(caz <= 0, pi - sun_azm, sun_azm) + pi', out=sun_azm)
    # ne.evaluate('rad2deg * where(sun_azm < 0, sun_azm + pi2, where(sun_azm >= pi2,
    #                                                         sun_azm - pi2, sun_azm))',
    #                                                                       out=sun_azm)
    LOG.info("Done calculating solar zenith and azimuth angles")

    return sun_zen, sun_azm
