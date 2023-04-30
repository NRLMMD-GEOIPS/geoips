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

"""Geotiff image rasterio-based output format."""

import os
import logging

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image"
name = "geotiff_standard"


def get_rasterio_cmap_dict(mpl_cmap, scale_data_min=1, scale_data_max=255):
    """Get rasterio cmap dict."""
    cmap_arr = mpl_cmap(range(0, 255)) * 255
    cmap_dict = {}
    for ii in range(0, 255):
        cmap_dict[ii] = tuple(cmap_arr[ii, :])
    return cmap_dict


def scale_geotiff_data(
    plot_data, mpl_colors_info, scale_data_min=1, scale_data_max=255, missing_value=0
):
    """Scale geotiff data."""
    from geoips.data_manipulations.corrections import apply_data_range

    min_val = None
    max_val = None
    inverse = False
    if (
        mpl_colors_info
        and "norm" in mpl_colors_info
        and hasattr(mpl_colors_info["norm"], "vmax")
    ):
        min_val = mpl_colors_info["norm"].vmin
        max_val = mpl_colors_info["norm"].vmax

    num_colors = scale_data_max - scale_data_min + 1

    scale_data = (
        scale_data_min
        + apply_data_range(
            plot_data, min_val=min_val, max_val=max_val, inverse=inverse, norm=True
        )
        * num_colors
    )
    scale_data.fill_value = missing_value
    return scale_data.filled()


def call(
    area_def,
    xarray_obj,
    product_name,
    output_fnames,
    product_name_title=None,
    mpl_colors_info=None,
    existing_image=None,
):
    """Create standard geotiff output using rasterio."""
    plot_data = scale_geotiff_data(
        xarray_obj[product_name].to_masked_array(), mpl_colors_info
    )
    import rasterio
    from affine import Affine

    for output_fname in output_fnames:
        from geoips.filenames.base_paths import make_dirs

        make_dirs(os.path.dirname(output_fname))
        with rasterio.Env():
            lons, lats = area_def.get_lonlats()

            height = plot_data.shape[0]
            width = plot_data.shape[1]

            res_deg_x = (lons[-1][-1] - lons[0][0]) / width
            res_deg_y = (lats[0][0] - lats[-1][-1]) / height

            minlat = area_def.area_extent_ll[1]
            minlon = area_def.area_extent_ll[0]

            transform = Affine.translation(
                minlon - res_deg_y / 2, minlat - res_deg_x / 2
            ) * Affine.scale(res_deg_y, res_deg_x)

            # crs = rasterio.crs.CRS.from_proj4(area_def.proj4_string)
            crs = "+proj=latlong"

            profile = rasterio.profiles.DefaultGTiffProfile(count=1)
            profile.update(dtype=rasterio.uint8, count=1, compress="lzw")

            with rasterio.open(
                output_fname,
                "w",
                width=width,
                height=height,
                crs=crs,
                transform=transform,
                **profile,
            ) as dst:
                dst.write(plot_data.astype(rasterio.uint8), indexes=1)
                cmap_dict = get_rasterio_cmap_dict(mpl_colors_info["cmap"])
                dst.write_colormap(1, cmap_dict)

    return output_fnames
