# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Utilities for working with YAML sector specifications."""

import logging

LOG = logging.getLogger(__name__)


def area_def_to_yamldict(area_def):
    """Convert passed pyresample AreaDefinition to a valid YAML dictionary."""
    yamldict = {}
    sectorname = str(area_def.area_id)
    yamldict[sectorname] = {}
    yamldict = add_sectorinfo_to_yamldict(
        yamldict, sectorname, dict(area_def.sector_info)
    )
    yamldict = add_description_to_yamldict(
        yamldict,
        sectorname,
        sector_type=area_def.sector_type,
        sector_start_datetime=area_def.sector_start_datetime,
        info_dict=dict(area_def.sector_info),
    )

    # The section below was commented out as it is not used by GeoIPS at this time, and
    # the function didn't work since it included errors. 9/27/23

    # yamldict = add_projection_to_yamldict(
    #     yamldict,
    #     sectorname,
    #     area_def.proj_dict["proj"],
    #     area_def.proj_dict["lat_0"],
    #     area_def.proj_dict["lon_0"],
    #     center_x=0,
    #     center_y=0,
    #     pix_x=area_def.x_size,
    #     pix_y=area_def.y_size,
    #     pix_width_m=area_def.pixel_size_x,
    #     pix_height_m=area_def.pixel_size_y,
    # )
    return yamldict


def area_def_to_yamlfile(area_def, out_fname):
    """Write pyresample AreaDefinition out as a valid YAML dictionary."""
    yamldict = area_def_to_yamldict(area_def)
    return write_yamldict(yamldict, out_fname=out_fname)


def write_yamldict(yamldict, out_fname, force=False):
    """Write yamldict to out_fname.

    Parameters
    ----------
    yamldict : dict
        Dictionary to write out to YAML file
    out_fname : str
        Output filename to write YAML dict to
    force : bool, default=False
        If True, overwrite existing file.

    Returns
    -------
    str
        Path to output file if successfully produced
    """
    from geoips.filenames.base_paths import make_dirs
    from os.path import dirname, exists
    import yaml

    make_dirs(dirname(out_fname))
    if not exists(out_fname) or force:
        with open(out_fname, "w") as fobj:
            LOG.info("SUCCESS Writing out yaml file %s", out_fname)
            yaml.safe_dump(yamldict, fobj, default_flow_style=False)
            return [out_fname]
    else:
        LOG.info(
            "SKIPPING %s already exists, delete it if you need to recreate", out_fname
        )
        return []


def add_dynamic_datetime_to_yamldict(
    yaml_dict, sectorname, sector_start_datetime, sector_end_datetime
):
    """Add passed dynamic datetime info to passed YAML dictionary."""
    yaml_dict[sectorname]["sector_start_datetime"] = sector_start_datetime
    yaml_dict[sectorname]["sector_end_datetime"] = sector_end_datetime
    return yaml_dict


def add_description_to_yamldict(
    yaml_dict, sectorname, sector_type, sector_start_datetime=None, info_dict=None
):
    """Add passed sector description information to passed YAML dictionary."""
    yaml_dict[sectorname]["sector_type"] = sector_type
    if sector_type == "static":
        yaml_dict[sectorname]["description"] = sectorname
    if sector_type == "tc":
        yaml_dict[sectorname]["sector_type"] = sector_type
        yaml_dict[sectorname]["description"] = "TC{0} {1}{2} {3} {4}".format(
            info_dict["storm_year"],
            info_dict["storm_basin"],
            info_dict["storm_num"],
            info_dict["storm_name"],
            str(info_dict["synoptic_time"]),
        )
    if sector_type in ["pyrocb", "atmosriver", "volcano"]:
        sector_start_datetime_str = yaml_dict[sectorname][
            "sector_start_datetime"
        ].strftime("%Y%m%dT%HZ")
        yaml_dict[sectorname]["sector_type"] = sector_type
        yaml_dict[sectorname]["description"] = "{0} at {1}".format(
            sectorname, sector_start_datetime_str
        )
    return yaml_dict


def add_sectorinfo_to_yamldict(yaml_dict, sectorname, sector_info_dict):
    """Add sector_info dictionary to YAML dictionary."""
    yaml_dict[sectorname]["sector_info"] = sector_info_dict
    return yaml_dict


# The function below were commented out as they included errors, and were not used
# by GeoIPS at this time. 9/27/23

# def add_projection_to_yamldict(
#     yaml_dict,
#     sectorname,
#     center_lat,
#     center_lon,
#     center_x=0,
#     center_y=0,
#     template_yaml=None,
# ):
#     """Add projection information to YAML dictionary."""
#     LOG.info("add_projection_to_yamldict - update to template_yaml")

#     yaml_dict[sectorname]["projection"] = {}
#     yaml_dict[sectorname]["projection"]["proj"] = proj
#     yaml_dict[sectorname]["projection"]["a"] = 6371228.0
#     yaml_dict[sectorname]["projection"]["units"] = "m"
#     yaml_dict[sectorname]["projection"]["lat_0"] = center_lat
#     yaml_dict[sectorname]["projection"]["lon_0"] = center_lon
#     yaml_dict[sectorname]["center"] = [center_x, center_y]
#     yaml_dict[sectorname]["resolution"] = [pix_width_m, pix_height_m]
#     # yaml_dict[sectorname]['shape'] = [pix_x, pix_y]
#     yaml_dict[sectorname]["shape"] = {}
#     yaml_dict[sectorname]["shape"]["width"] = pix_x
#     yaml_dict[sectorname]["shape"]["height"] = pix_y
#     # This only works because it is square!!
#     yaml_dict[sectorname]["area_extent"] = {
#         "lower_left_xy": [
#             center_x - (pix_x * pix_width_m / 2),
#             center_y - (pix_y * pix_height_m / 2),
#         ],
#         "upper_right_xy": [
#             center_x + (pix_x * pix_width_m / 2),
#             center_y + (pix_y * pix_height_m / 2),
#         ],
#     }
#     return yaml_dict
