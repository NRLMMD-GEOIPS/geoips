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

''' Module containing matplotlib information for standard imagery with an existing system colormap'''
import logging

LOG = logging.getLogger(__name__)

cmap_type = 'builtin_matplotlib_cmap'


def matplotlib_linear_norm(data_range, cmap_name='Greys', cbar_label=None, create_colorbar=True, cbar_ticks=None):
    ''' Set the matplotlib colors information appropriately, for use in colorbar and image production.

    Args:
        data_range (list) : [min_val, max_val]
        cmap_name (str) : Default 'Greys' - specify the standard matplotlib colormap.
        cbar_label (str) : Default None - If specified, use cbar_label string as colorbar label.
        create_colorbar (bool) : Default True - Specify whether the image should contain a colorbar or not.
        cbar_ticks (list) : Default None - Specify explicit list of ticks to include for colorbar.
                                     None indicates ticks at int(min) and int(max) values

    Returns:
        mpl_colors_info (dict) Specifies matplotlib Colors parameters for use in both plotting and colorbar generation
                                See geoips.image_utils.mpl_utils.create_colorbar for field descriptions.
    '''

    min_val = data_range[0]
    max_val = data_range[1]

    from matplotlib import cm
    # cmap = cm.ScalarMappable(norm=colors.NoNorm(), cm.get_cmap(cmap_name))
    mpl_cmap = cm.get_cmap(cmap_name)

    LOG.info('Setting norm')
    from matplotlib.colors import Normalize
    mpl_norm = Normalize(vmin=min_val, vmax=max_val)
    if cbar_ticks:
        mpl_ticks = cbar_ticks
    else:
        mpl_ticks = [int(min_val), int(max_val)]

    # Must be uniform or proportional, None not valid for Python 3
    cbar_spacing = 'proportional'
    mpl_tick_labels = None
    mpl_boundaries = None

    mpl_colors_info = {'cmap': mpl_cmap,
                       'norm': mpl_norm,
                       'cbar_ticks': mpl_ticks,
                       'cbar_tick_labels': mpl_tick_labels,
                       'cbar_label': cbar_label,
                       'boundaries': mpl_boundaries,
                       'cbar_spacing': cbar_spacing,
                       'colorbar': create_colorbar}

    return mpl_colors_info
