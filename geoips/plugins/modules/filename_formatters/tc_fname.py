# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard TC filename formatter."""

# Python Standard Libraries
import logging

from os.path import join as pathjoin, splitext as pathsplitext
from os.path import (
    dirname as pathdirname,
    basename as pathbasename,
)
from datetime import datetime, timedelta
from glob import glob
from os import unlink as osunlink

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.data_manipulations.merge import minrange

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "standard"
name = "tc_fname"


def call(
    area_def,
    xarray_obj,
    product_name,
    coverage=None,
    output_type="png",
    output_type_dir=None,
    basedir=gpaths["TCWWW"],
    extra_field=None,
    output_dict=None,
):
    """Create standard TC filenames.

    See Also
    --------
    geoips.plugins.modules.filename_formatters.tc_fname.assemble_tc_fname
        This uses the shared utility "assemble_tc_fname", such that a common
        filename can be used by related filename formatters.
    """
    from geoips.sector_utils.utils import is_sector_type

    if area_def and not is_sector_type(area_def, "tc"):
        LOG.warning("NOT a TC sector, skipping TC output")
        return None

    # Allow output_type_dir to be explicitly set within call signature, allows
    # derivative filename formatters to set alternative output_type_dir values.
    # This is currently used by tc_clean_fname.py to write to e.g. png_clean
    # vs png directories.
    if not output_type_dir:
        output_type_dir = output_type

    # This allows you to explicitly set matplotlib parameters (colorbars, titles, etc).
    # Overrides were placed in geoimgbase.py to allow using explicitly set values
    # rather than geoimgbase determined defaults.
    # Return reused parameters (min/max vals for normalization, colormaps,
    # matplotlib Normalization)
    # from geoips.xarray_utils.time import get_min_from_xarray_time
    # start_dt = get_min_from_xarray_time(xarray_obj, 'time')
    start_dt = xarray_obj.start_datetime

    if area_def.sector_info["vmax"]:
        intensity = "{0:0.0f}kts".format(area_def.sector_info["vmax"])
    else:
        # This is pulling intensity directly from the deck file,
        # and sometimes it is not defined - if empty, just
        # use "unknown" for intensity
        intensity = "unknown"

    from geoips.plugins.modules.filename_formatters.utils.tc_file_naming import (
        update_extra_field,
    )

    extra = update_extra_field(
        output_dict,
        xarray_obj,
        area_def,
        product_name,
        extra_field_delimiter="-",
        existing_extra_field=extra_field,
        extra_field_resolution=True,
        extra_field_coverage_func=True,
        extra_field_provider=False,
        include_filename_extra_fields=True,
    )

    web_fname = assemble_tc_fname(
        basedir=basedir,
        output_type=output_type,
        product_name=product_name,
        source_name=xarray_obj.source_name,
        platform_name=xarray_obj.platform_name,
        coverage=coverage,
        product_datetime=start_dt,
        intensity=intensity,
        extra=extra,
        output_type_dir=output_type_dir,
        sector_info=area_def.sector_info,
    )

    return web_fname


def tc_fname_remove_duplicates(fname, mins_to_remove=3, remove_files=False):
    """Remove tc_fname duplicate files.

    Matches storm name, sensor name, platform name, product name, and
    resolution for all files within "mins_to_remove" minutes of the
    current file.  All other fields are wild carded during the matching
    process.
    """
    # 20201010_222325_WP162020_gmi_GPM_89H_40kts_14p16_1p0.png
    # 20201010_222325_WP162020_gmi_GPM_89H_40kts_14p16_1p0.png.yaml
    matching_fnames = []
    removed_fnames = []
    saved_fnames = []
    ext1 = pathsplitext(fname)[-1]
    ext2 = pathsplitext(pathsplitext(fname)[0])[-1]
    # ext3 = pathsplitext(pathsplitext(pathsplitext(fname)[0])[0])[-1]
    if (ext1 == ".png") or (ext1 == ".yaml" and ext2 == ".png"):
        LOG.info(
            "MATCHES EXT FORMAT. png or png.yaml. "
            "Attempting to remove old_tcweb duplicates"
        )
    else:
        LOG.info("NOT REMOVING DUPLICATES. Not tc_web filename, not png or png.yaml.")
        return [], []
    dirname = pathdirname(fname)
    basename = pathbasename(fname)
    parts = basename.split("_")
    if len(parts) != 9:
        LOG.info(
            "NOT REMOVING DUPLICATES. Not tc_web filename, does not contain 9 fields."
        )
        return [], []

    try:
        # 20201010_222325_WP162020_gmi_GPM_89H_40kts_14p16_1p0.png
        yyyymmdd = parts[0]
        hhmnss = parts[1]
        stormname = parts[2]
        sensor = parts[3]
        platform = parts[4]
        product = parts[5]
        intensity = parts[6]
        coverage = parts[7]
        res = parts[8]
        if "p" not in coverage or "p" not in res:
            LOG.info(
                "NOT REMOVING DUPLICATES. Not tc_web filename, "
                "coverage or res not 'NNpNN'."
            )
            return [], []
        if "kts" not in intensity:
            LOG.info(
                "NOT REMOVING DUPLICATES. Not tc_web filename, "
                "intensity does not contain 'kts'."
            )
            return [], []
    except IndexError:
        LOG.info(
            "NOT REMOVING DUPLICATES. Unmatched filename format, "
            "incorrect number of _ delimited fields"
        )
        return [], []
    try:
        fname_dt = datetime.strptime(yyyymmdd + hhmnss, "%Y%m%d%H%M%S")
    except ValueError:
        LOG.info(
            "NOT REMOVING DUPLICATES. Unmatched filename format, "
            "incorrect date time string."
        )
        return [], []
    timediff = timedelta(minutes=mins_to_remove)
    for currdt in minrange(fname_dt - timediff, fname_dt + timediff):
        # 20201010_222325_WP162020_gmi_GPM_89H_40kts_14p16_1p0.png
        dtstr = currdt.strftime(
            "{0}/%Y%m%d_%H%M*_{1}_{2}_{3}_{4}_*_*_{5}".format(
                dirname, stormname, sensor, platform, product, res
            )
        )
        # LOG.info(dtstr)
        matching_fnames += glob(dtstr)
    max_coverage = 0
    min_dt = None
    for matching_fname in matching_fnames:
        # 20201010_222325_WP162020_gmi_GPM_89H_40kts_14p16_1p0.png
        parts = pathbasename(matching_fname).split("_")
        coverage = float(parts[7].replace("p", "."))
        start_dt = datetime.strptime(parts[0] + parts[1][0:6], "%Y%m%d%H%M%S")
        max_coverage = max(coverage, max_coverage)
        if min_dt is None:
            min_dt = start_dt
        else:
            min_dt = min(start_dt, min_dt)

    gotone = False
    LOG.info("CHECKING DUPLICATE FILES")
    for matching_fname in list(set(matching_fnames)):
        # 20201010_222325_WP162020_gmi_GPM_89H_40kts_14p16_1p0.png
        parts = pathbasename(matching_fname).split("_")
        coverage = float(parts[7].replace("p", "."))
        start_dt = datetime.strptime(parts[0] + parts[1][0:6], "%Y%m%d%H%M%S")
        # Priority to delete lower coverage
        if coverage < max_coverage:
            removed_fnames += [matching_fname]
            # Test it out for a bit first
            if remove_files is True:
                LOG.info(
                    "DELETING DUPLICATE FILE with less coverage %s < %s %s",
                    coverage,
                    max_coverage,
                    matching_fname,
                )
                try:
                    osunlink(matching_fname)
                except FileNotFoundError as resp:
                    LOG.warning(
                        "FAILDELETE %s: File %s did not exist, "
                        "someone must have deleted it for us?",
                        matching_fname,
                        str(resp),
                    )

            else:
                LOG.info(
                    "TEST DELETING DUPLICATE FILE with less coverage %s < %s %s",
                    coverage,
                    max_coverage,
                    matching_fname,
                )
        elif start_dt > min_dt:
            removed_fnames += [matching_fname]
            # Test it out for a bit first
            if remove_files is True:
                LOG.info(
                    "DELETING DUPLICATE FILE with later start_dt %s > %s %s",
                    start_dt,
                    min_dt,
                    matching_fname,
                )
                try:
                    osunlink(matching_fname)
                except FileNotFoundError as resp:
                    LOG.warning(
                        "FAILDELETE %s: File %s did not exist, "
                        "someone must have deleted it for us?",
                        matching_fname,
                        str(resp),
                    )

            else:
                LOG.info(
                    "TEST DELETING DUPLICATE FILE with later start_dt %s > %s %s",
                    start_dt,
                    min_dt,
                    matching_fname,
                )
        elif gotone is True:
            removed_fnames += [matching_fname]
            # Test it out for a bit first
            if remove_files is True:
                LOG.info(
                    "DELETING DUPLICATE FILE with same coverage %s = %s "
                    "and same start_dt %s = %s, %s",
                    coverage,
                    max_coverage,
                    start_dt,
                    min_dt,
                    matching_fname,
                )
                try:
                    osunlink(matching_fname)
                except FileNotFoundError as resp:
                    LOG.warning(
                        "FAILDELETE %s: File %s did not exist, "
                        "someone must have deleted it for us?",
                        matching_fname,
                        str(resp),
                    )

            else:
                LOG.info(
                    "TEST DELETING DUPLICATE FILE with same coverage %s = %s "
                    "and same start_dt %s = %s, %s",
                    coverage,
                    max_coverage,
                    start_dt,
                    min_dt,
                    matching_fname,
                )
        else:
            if len(matching_fnames) == 1:
                LOG.info(
                    "SAVING DUPLICATE FILE (only one!) with max coverage %s %s",
                    max_coverage,
                    matching_fname,
                )
            else:
                LOG.info(
                    "SAVING DUPLICATE FILE with max coverage %s %s",
                    max_coverage,
                    matching_fname,
                )
            saved_fnames += [matching_fname]
            gotone = True

    return removed_fnames, saved_fnames


def assemble_tc_fname(
    basedir,
    output_type,
    product_name,
    source_name,
    platform_name,
    coverage,
    product_datetime,
    intensity=None,
    extra=None,
    output_type_dir=None,
    sector_info=None,
):
    """Produce full output product path from product / sensor specifications.

    tc web paths are of the format:
        <basedir>/tc<tc_year>/<tc_basin>/<storm_id>/
          <output_type>/<product_name>/<platform_name>/
    tc web filenames are of the format:
        <date{%Y%m%d%H%M>_<tc_basin><tc_stormnum><tc_year>_<source_name>_
          <platform_name>_<product_name>_<intensity>_<coverage>_
          <extra>.<output_type>

    Note paths use full storm id (e.g., include storm start datetime
    for invests), but filenames use simplified BBNNYYYY without storm
    start datetime.

    Parameters
    ----------
    basedir : str
        Base directory for output file.
    output_type : str
        file extension type
    product_name : str
        Name of product
    source_name : str
        Name of data source (sensor)
    platform_name : str
        Name of platform (satellite)
    coverage : float
        Image coverage, float between 0.0 and 100.0
    product_datetime : datetime.datetime
        Datetime object - start time of data used to generate product
    output_type_dir : str, default None
        If None, default to output_type. Sub-Directory name for output file type.
        Allow output_type_dir to be explicitly set within call signature, allows
        derivative filename formatters to set alternative output_type_dir values.
        This is currently used by tc_clean_fname.py to write to e.g. png_clean
        vs png directories. Remove support for explicitly setting product_dir,
        product_subdir, or source_dir - if alternative filename composition is
        required, create an alternative filename formatter plugin.

    Returns
    -------
    str
        full path to output file
    """
    if not output_type_dir:
        output_type_dir = output_type

    from geoips.plugins.modules.filename_formatters.utils.tc_file_naming import (
        tc_storm_basedir,
    )

    # Note we no longer support alternative output_type_dir, product_dir, or
    # product_subdir - if alternative filename composition is required, create
    # an alternative filename formatter plugin.
    path = pathjoin(
        tc_storm_basedir(basedir, sector_info),
        output_type_dir,
        product_name,
        platform_name,
    )
    # Internal storm_ids: al202020 -> AL202020, sh9820212021062400 -> SH982021
    # * storm_ids are stored internally as lower case, upper case for filenames.
    # * Do NOT include storm_start_datetime for invests in filenames (though we
    #   use the full storm_id, include storm start datetime, in the file path
    #   subdirectories)
    bbnnyyyy = sector_info["storm_id"][0:8].upper()
    fname = "_".join(
        [
            product_datetime.strftime("%Y%m%d"),
            product_datetime.strftime("%H%M%S"),
            bbnnyyyy,
            source_name,
            platform_name,
            product_name,
            str(intensity),
            "{0:0.2f}".format(coverage).replace(".", "p"),
            str(extra),
        ]
    )
    fname = "{0}.{1}".format(fname, output_type)
    return pathjoin(path, fname)
