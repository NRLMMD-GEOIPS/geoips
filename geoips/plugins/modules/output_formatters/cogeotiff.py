# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geotiff image rasterio-based output format."""

import os
import logging

import numpy
from affine import Affine
from rasterio.io import MemoryFile
from rasterio import uint8

# from rasterio.transform import from_bounds
from rasterio.plot import reshape_as_raster

# from rasterio.enums import ColorInterp
import rasterio
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

# from pyresample.utils import wrap_longitudes

# Internal utilities
from geoips.errors import (
    OutputFormatterInvalidProjectionError,
    OutputFormatterDatelineError,
)
from geoips.filenames.base_paths import make_dirs

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image"
name = "cogeotiff"


def get_rasterio_cmap_dict(
    mpl_cmap, scale_data_min=1, scale_data_max=255, missing_value=0
):
    """Get rasterio cmap dict, with vals between scale_data_min and scale_data_max."""
    # Scale from 1 to 255, leave 0 for missing value.
    cmap_arr = mpl_cmap(range(scale_data_min, scale_data_max)) * scale_data_max
    cmap_dict = {}
    arr_ind = 0
    # Get the actual RGBA values for each of the values in the colormap, with
    # a total number of colors between scale_data min and scale_data_max.
    for ii in range(scale_data_min, scale_data_max):
        cmap_dict[ii] = tuple(cmap_arr[arr_ind, :])
        arr_ind += 1
    # RGB values don't matter, just the "0" for the masked part.
    cmap_dict[missing_value] = (0, 255.0, 255.0, 0.0)
    return cmap_dict


def get_scales_and_offsets(
    bands, requested_data_min, requested_data_max, scale_data_min, scale_data_max
):
    """Get scale and offset information from dataset.

    These values are written to the geotiff file metadata in order to use for
    retrieving quantitative values from the scaled data when rendering.
    """
    scales = []
    offsets = []
    for band in range(bands):
        if requested_data_min is not None and requested_data_max is not None:
            scale = (requested_data_max - requested_data_min) / (
                scale_data_max - scale_data_min
            )
            offset = requested_data_min - scale * float(scale_data_min)
        else:
            scale = 1.0
            offset = 0.0
        scales += [scale]
        offsets += [offset]
    return scales, offsets


def scale_geotiff_data(
    plot_data, mpl_colors_info, scale_data_min=1, scale_data_max=255, missing_value=0
):
    """Scale geotiff data between scale_data_min and scale_data_max."""
    from geoips.data_manipulations.corrections import apply_data_range

    bands = 1
    if len(plot_data.shape) == 3:
        bands = plot_data.shape[2]

    alpha = None
    if bands == 4:
        # Only scale RGB bands
        bands = 3
        # Pull out the alpha layer, should be 0 or 255. Starts as 0 or 1.
        # 1 + scale*254, for range 1 to 255
        alpha = plot_data[:, :, 3] * 255

    min_val = None
    max_val = None
    inverse = False
    # Use the min and max values in mpl_colors_info norm if specified.
    if (
        mpl_colors_info
        and "norm" in mpl_colors_info
        and hasattr(mpl_colors_info["norm"], "vmax")
    ):
        min_val = mpl_colors_info["norm"].vmin
        max_val = mpl_colors_info["norm"].vmax

    # This is 254 for range 1 to 255.
    num_colors = scale_data_max - scale_data_min

    # Get the scales and offsets for the non-alpha layer.
    scales, offsets = get_scales_and_offsets(
        bands, min_val, max_val, scale_data_min, scale_data_max
    )

    if bands == 1:
        # Just get the scale data with one band
        scale_data = (
            scale_data_min
            + apply_data_range(
                plot_data, min_val=min_val, max_val=max_val, inverse=inverse, norm=True
            )
            * num_colors
        )
    else:
        # This is RGBA, get scaled data for each band
        for band in range(bands):
            curr_scale_data = (
                scale_data_min
                + apply_data_range(
                    plot_data[:, :, band],
                    min_val=min_val,
                    max_val=max_val,
                    inverse=inverse,
                    norm=True,
                )
                * num_colors
            )
            #
            if band == 0:
                scale_data = curr_scale_data
            else:
                scale_data = numpy.dstack((scale_data, curr_scale_data))

    # Add the alpha layer back on.
    if alpha is not None:
        scale_data = numpy.dstack((scale_data, alpha))
        scales += [1.0]
        offsets += [0.0]

    # Set the missing value
    scale_data.fill_value = missing_value
    return scale_data.filled(), missing_value, scales, offsets


def get_geotiff_transform(area_def):
    """Get the appropriate GeoTIFF transform and projectio information."""
    # Note the original implementation here, following the
    # rasterio documentation, resulted in upside down imagery.
    # https://github.com/rasterio/rasterio/issues/1683
    # Updates 20231005 resolved the flipped geotiff imagery.

    # Some notes on geotiff lat/lon ranges:
    # * -180 to 180 longitude range works, anything outside that range will get
    #   cut off (for longlat / 4326)
    # * -90 to 90 latitude range works, but if you go outside that range at all,
    #   the image will not display at all
    # * Affine transform will NOT work if you cross the dateline for 4326,
    #   because of the above
    # * I am not 100% sure if there is a way to define the 4326 projection
    #   to allow crossing the dateline, perhaps if we cross the dateline we
    #   would have to reproject using a different prime meridian?

    # These should be the same as area_extent_ll
    # lons, lats = area_def.get_lonlats()
    # bottom_right_lon = wrap_longitudes(lons[-1][-1])
    # bottom_left_lon = wrap_longitudes(lons[-1][0])
    # top_left_lon = wrap_longitudes(lons[0][0])
    # top_right_lon = wrap_longitudes(lons[0][-1])

    height = area_def.height
    width = area_def.width

    # Note this may need an additional check that the units are in meters for
    # eqc, and units in degrees for longlat projection.  This really requires
    # very specifically set up area definitions that match what cogeotiff is
    # expecting.  I expect we will just add additional try/excepts, and error
    # if the area definition is not of the correct format, rather than adding
    # more supported cases.  We should think carefully about what projections/
    # area definition formats we want to handle / support.
    if area_def.proj_dict["proj"] == "eqc":
        # For eqc projection, area_extent is in m, and area_extent_ll in degrees
        minlat = area_def.area_extent_ll[1]
        maxlat = area_def.area_extent_ll[3]
        minlon = area_def.area_extent_ll[0]
        maxlon = area_def.area_extent_ll[2]
        # Pulling crs from area def did not work for the standard eqc sectors.
        crs = "EPSG:4326"
    elif area_def.proj_dict["proj"] == "longlat":
        # For longlat projection, area_extent is actually in degrees
        minlat = area_def.area_extent[1]
        maxlat = area_def.area_extent[3]
        minlon = area_def.area_extent[0]
        maxlon = area_def.area_extent[2]
        # Pulling crs from area def worked for the longlat projections
        crs = rasterio.crs.CRS.from_proj4(area_def.proj4_string)

    # We may want to add additional checks to ensure sectors are set up properly.
    if maxlon < 0 and minlon > maxlon:
        raise OutputFormatterDatelineError(
            "Region CAN NOT cross the dateline. "
            "Try again with a different sector."
            "Note you can create a projection 'longlat' area_def with the "
            "prime meridian set to the center of the sector with the 'pm' field, "
            "which will allow creating sectors that cross the IDL."
        )

    # Determine the transform based on min/max lat/lon, and width/height.
    res_deg_x = abs(maxlon - minlon) / (width)
    res_deg_y = (maxlat - minlat) / (height)
    src_transform = Affine(res_deg_x, 0, minlon, 0, -res_deg_y, maxlat)

    # Return resulting projection information
    return height, width, crs, src_transform


def call(
    area_def,
    xarray_obj,
    product_name,
    output_fnames,
    product_name_title=None,
    mpl_colors_info=None,
    existing_image=None,
    cog=True,
):
    """Create standard geotiff output using rasterio."""
    # We may want to add additional checks to ensure projections are set up
    # properly for what is explicitly supported in the cogeotiff output formatter,
    # for now it at least requires eqc or longlat, and there must be no lat/lon
    # values outside the -180 to 180 range. There are probably additional
    # requirements for those projections, so we should add to the checks as
    # those requirements are identified.
    if area_def.proj_dict["proj"] not in ["eqc", "longlat"]:
        raise OutputFormatterInvalidProjectionError(
            "Projection must be 'eqc' in order to produce COGS output. "
            "This writer relies on equally spaced lat/lons"
        )

    # Scale the data to produce an 8 bit geotiff.  Defaults to range 1 to 255
    # with missing value of 0.
    plot_data, missing_value, scales, offsets = scale_geotiff_data(
        xarray_obj[product_name].to_masked_array(), mpl_colors_info
    )

    # https://cogeotiff.github.io/rio-cogeo/API/

    with MemoryFile() as memfile:

        # Get the CRS and transform information based on the current area
        # definition.  GeoTIFFs are fairly particular about how the projection
        # information is specified.  Ie, you can't go outside -180 to 180.
        height, width, crs, src_transform = get_geotiff_transform(area_def)

        # If this is RGBA data, e.g. shape is (bands, width, height),
        # then reshape the data as required to write out to geotiff.
        if len(plot_data.shape) == 3 and plot_data.shape[2] == 4:
            is_rgba = True
            bands = plot_data.shape[2]
            plot_data = reshape_as_raster(plot_data.astype(uint8))
            indexes = ()
            for i in range(bands):
                indexes += (i + 1,)
        # Otherwise, we just have a single channel, one band and one index.
        else:
            is_rgba = False
            bands = 1
            indexes = 1

        # Profile for writing the GeoTIFF, using information obtained above.
        src_profile = dict(
            driver="GTiff",
            dtype=uint8,
            count=bands,
            height=height,
            width=width,
            crs=crs,
            transform=src_transform,
        )

        # Initially open the file in memory, based on the above profile.
        with memfile.open(**src_profile) as mem:

            # If this is not RGBA, then set up the internal colormap information.
            if not is_rgba:
                # Populate the input file with numpy array
                cmap_dict = get_rasterio_cmap_dict(mpl_colors_info["cmap"])
                # Must set nodata prior to writing colormap for cog_translate
                mem.nodata = missing_value
                mem.write_colormap(1, cmap_dict)

            # Write out the data to the in-memory GeoTIFF, with the appropriate
            # indexes.
            # masked=True ensures the alpha layer is written to the GeoTIFF,
            # if it is available.  If there is no alpha layer, masked=True
            # has no impact.
            mem.write(plot_data.astype(uint8), indexes=indexes)
            mem.scales = scales
            mem.offsets = offsets

            # This seems to be the default
            # if is_rgba:
            #     mem.colorinterp = [
            #           ColorInterp.red,
            #           ColorInterp.green,
            #           ColorInterp.blue,
            #           ColorInterp.alpha]

            # Adding this explicitly definitely caused more overviews to be
            # created, but I am not sure we want that.  It should come up with
            # reasonable defaults on it's own, and for the very large high
            # resolution sectors we definitely will get more than 3 overviews.
            # if cog:
            #     mem.build_overviews([1, 2, 3])

            dst_profile = cog_profiles.get("deflate")
            for output_fname in output_fnames:
                make_dirs(os.path.dirname(output_fname))
                cog_translate(
                    mem,
                    output_fname,
                    dst_profile,
                    # This should be auto-determined, and I don't think we will
                    # ever want to hard code it here.  Large high resolution
                    # sectors should always end up with more than 3 overviews.
                    # overview_level=3,
                    in_memory=True,
                    quiet=True,
                )
            LOG.info(f"cogeotiff {output_fname}")

    return output_fnames
