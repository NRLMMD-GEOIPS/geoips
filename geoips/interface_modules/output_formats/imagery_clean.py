# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

import os
import logging

LOG = logging.getLogger(__name__)

output_type = 'image'

def imagery_clean(area_def,
                  xarray_obj,
                  product_name,
                  output_fnames,
                  product_name_title=None,
                  mpl_colors_info=None,
                  existing_image=None,
                  remove_duplicate_minrange=None):

    success_outputs = []
    plot_data = xarray_obj[product_name].to_masked_array()
    from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
    from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard
    from geoips.image_utils.mpl_utils import plot_image, save_image

    if not mpl_colors_info:
        # Create the matplotlib color info dict - the fields in this dictionary (cmap, norm, boundaries,
        # etc) will be used in plot_image to ensure the image matches the colorbar.
        mpl_colors_info = set_matplotlib_colors_standard(data_range=[plot_data.min(), plot_data.max()],
                                                         cmap_name=None,
                                                         cbar_label=None)
    mapobj = None

    for clean_fname in output_fnames:
        # Create matplotlib figure and main axis, where the main image will be plotted
        fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(area_def.x_size,
                                                                    area_def.y_size,
                                                                    area_def,
                                                                    noborder=True)
   
        # Plot the actual data on a map
        plot_image(main_ax,
                   plot_data,
                   mapobj,
                   mpl_colors_info=mpl_colors_info)

        LOG.info('Saving the clean image %s', clean_fname)
        # Save the clean image with no gridlines or coastlines
        success_outputs += save_image(fig, clean_fname, is_final=False, image_datetime=xarray_obj.start_datetime,
                                      remove_duplicate_minrange=remove_duplicate_minrange)

    return success_outputs

