# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Generate standard pyresample area definitions given center coordinates.

Given desired center lat/lon, projection, resolution, and shape, return a
valid pyresample area definition object.
"""

interface = "sector_spec_generators"
family = "area_definition"
name = "center_coordinates"


def set_clat_clon_proj_info(
    clat, clon, pr_proj, num_samples, num_lines, pixel_width, pixel_height
):
    """Create standard proj4 dictionary from passed projection information."""
    width_m = num_samples * pixel_width
    height_m = num_lines * pixel_height

    proj4_dict = {
        "proj": pr_proj,
        "a": 6371228.0,
        "lat_0": clat,
        "lon_0": clon,
        "units": "m",
    }
    area_left = -width_m / 2.0
    area_right = width_m / 2.0
    area_bot = -height_m / 2.0
    area_top = height_m / 2.0
    area_extent = (area_left, area_bot, area_right, area_top)
    return proj4_dict, area_extent


def call(
    area_id,
    long_description,
    clat,
    clon,
    projection,
    pixel_width,
    pixel_height,
    num_samples,
    num_lines,
):
    """Create area definition using clat, clon, resolution, and shape."""
    proj4_dict, area_extent = set_clat_clon_proj_info(
        clat=clat,
        clon=clon,
        pr_proj=projection,
        num_samples=num_samples,
        num_lines=num_lines,
        pixel_width=pixel_width,
        pixel_height=pixel_height,
    )

    # Create the AreaDefinition object from given fields.
    # We are currently relying on Sector objects
    # for some information - need to decide how to handle this directly.
    # This is area_id= then name= for Python2, area_id= then description= for Python3
    from pyresample import AreaDefinition

    try:
        # Backwards compatibility for Python 2 version of pyresample
        area_def = AreaDefinition(
            area_id,
            long_description,
            proj_id="{0}_{1}".format(proj4_dict["proj"], area_id),
            proj_dict=proj4_dict,
            x_size=num_samples,
            y_size=num_lines,
            area_extent=area_extent,
        )
    except TypeError:
        area_def = AreaDefinition(
            area_id,
            long_description,
            proj_id="{0}_{1}".format(proj4_dict["proj"], area_id),
            projection=proj4_dict,
            width=num_samples,
            height=num_lines,
            area_extent=area_extent,
        )
    return area_def
