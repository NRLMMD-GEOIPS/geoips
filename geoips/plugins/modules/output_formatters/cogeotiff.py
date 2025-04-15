# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geotiff image rasterio-based output format."""

import os
import logging

# Internal utilities
from geoips.errors import OutputFormatterDatelineError
from geoips.errors import OutputFormatterInvalidProjectionError

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image"
name = "cogeotiff"


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
    if area_def.proj_dict["proj"] != "eqc":
        raise OutputFormatterInvalidProjectionError(
            "Projection must be 'eqc' in order to produce COGS output. "
            "This writer relies on equally spaced lat/lons"
        )
    plot_data = scale_geotiff_data(
        xarray_obj[product_name].to_masked_array(), mpl_colors_info
    )
    from rasterio.io import MemoryFile
    from rasterio import uint8

    # from rasterio.transform import from_bounds
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    # https://cogeotiff.github.io/rio-cogeo/API/
    from affine import Affine

    for output_fname in output_fnames:
        from geoips.filenames.base_paths import make_dirs

        make_dirs(os.path.dirname(output_fname))
        with MemoryFile() as memfile:

            # lons, lats = area_def.get_lonlats()

            # Rasterio uses numpy array of shape of `(bands, height, width)`
            height = plot_data.shape[0]
            width = plot_data.shape[1]
            if len(plot_data) == 3:
                bands = plot_data.shape[2]
                LOG.debug(bands)
            minlat = area_def.area_extent_ll[1]
            maxlat = area_def.area_extent_ll[3]

            minlon = area_def.area_extent_ll[0]
            maxlon = area_def.area_extent_ll[2]
            # Updated for crossing dateline
            if maxlon < 0 and minlon > maxlon:
                maxlon += 360
                raise OutputFormatterDatelineError(
                    "Region CAN NOT cross the dateline. "
                    "Try again with a different sector"
                )

            res_deg_x = abs(maxlon - minlon) / (width)
            # If we do not add one to height, the calculated min
            # for the lat extends slightly past the range.
            res_deg_y = (maxlat - minlat) / (height + 1)

            # Note the original implementation here, following the
            # rasterio documentation, resulted in upside down imagery.
            # https://github.com/rasterio/rasterio/issues/1683
            # Updates 20231005 resolved the flipped geotiff imagery.
            # Updates 20240322 discovered the rasterio documentation was
            # probably correct, need to flip back.
            # Flipped
            src_transform = Affine.translation(
                minlon - res_deg_x / 2, maxlat - res_deg_y / 2
            ) * Affine.scale(res_deg_x, -res_deg_y)
            # Orig
            # src_transform = Affine.translation(
            #     minlon - res_deg_y / 2, minlat - res_deg_x / 2
            # ) * Affine.scale(res_deg_y, res_deg_x)

            # crs = rasterio.crs.CRS.from_proj4(area_def.proj4_string)
            # Test with "EPSG:4326" crs
            # crs = "EPSG:4326"
            # Flipped
            crs = "+proj=longlat"
            # Orig
            # crs = "+proj=latlong"
            src_profile = dict(
                driver="GTiff",
                dtype=uint8,
                count=1,
                height=height,
                width=width,
                crs=crs,
                transform=src_transform,
            )

            with memfile.open(**src_profile) as mem:
                # Populate the input file with numpy array
                cmap_dict = get_rasterio_cmap_dict(mpl_colors_info["cmap"])
                mem.write_colormap(1, cmap_dict)
                mem.write(plot_data.astype(uint8), indexes=1)

                dst_profile = cog_profiles.get("deflate")
                cog_translate(
                    mem,
                    output_fname,
                    dst_profile,
                    in_memory=True,
                    quiet=True,
                )
                # from IPython import embed as shell; shell()

    return output_fnames
