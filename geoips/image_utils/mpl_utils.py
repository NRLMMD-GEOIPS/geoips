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

''' matplotlib utilities '''

# Python Standard Libraries
import logging
import matplotlib

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)


def percent_unmasked_rgba(rgba):
    ''' Return percentage of array that is NOT fully transparent / masked (ie, non-zero values in the 4th dimension)

    Args:
        rgba (numpy.ndarray) : 4 dimensional array where the 4th dimension is the alpha transparency array:
                               1 is fully opaque, 0 is fully transparent

    Returns:
        float : Coverage in percentage, between 0 and 100.
    '''
    import numpy
    return 100.0 * numpy.count_nonzero(rgba[:, :, 3]) / rgba[:, :, 3].size


def rgba_from_arrays(red, grn, blu, alp=None):
    ''' Return rgba for plotting in matplot lib from red, green, blue, and alpha arrays

    Args:
        red (numpy.ndarray) : numpy masked array of red gun values
        grn (numpy.ndarray) : numpy masked array of green gun values
        blu (numpy.ndarray) : numpy masked array of blue gun values
        alp (numpy.ndarray) : DEFAULT None, numpy.ndarray of alpha values 1 is fully opaque, 0 is fully transparent
                                If none, calculate alpha from red, grn, blu guns

    Returns:
        (numpy.ndarray) : 4 layer dimensional numpy.ndarray
    '''

    import numpy
    if alp is None:
        alp = alpha_from_masked_arrays([red, grn, blu])
    red.fill_value = 0
    grn.fill_value = 0
    blu.fill_value = 0
    return numpy.dstack([red.filled(), grn.filled(), blu.filled(), alp])


def alpha_from_masked_arrays(arrays):
    ''' Return an alpha transparency array based on the masks from a list of masked arrays. 0=transparent, 1=opaque

    Args:
        arrays (list): list of numpy masked arrays, must all be the same shape

    Returns:
        numpy.ndarray : Returns a numpy array of floats to be used as the alpha transparency layer in matplotlib,
                          values between 0 and 1, where
                            0 is fully transparent and
                            1 is fully opaque
    '''
    import numpy
    alp = numpy.zeros(arrays[0].shape, dtype=numpy.bool)
    for img in arrays:
        try:
            if img.mask is not numpy.False_:
                alp += img.mask
        except AttributeError:
            pass
    # You will get yelled at by numpy if you removed the "alp.dtype" portion of this.
    #   It thinks you are trying to cast alp to be an integer.
    alp = numpy.array(alp, dtype=numpy.float)
    alp -= numpy.float(1)
    alp *= numpy.float(-1)
    return alp


def plot_overlays(mapobj, curr_ax, area_def, boundaries_info, gridlines_info,
                  boundaries_zorder=None, gridlines_zorder=None):
    ''' Plot specified coastlines and gridlines on the matplotlib axes.

    Args:
        mapobj (map object): Basemap or CRS object for boundary and gridline plotting.
        ax (matplotlib.axes._axes.Axes): matplotlib Axes object for boundary and gridline plotting.
        area_def (AreaDefinition) : pyresample AreaDefinition object specifying the area covered by the current plot
        boundaries_info (dict) : Dictionary of parameters for plotting map boundaries.
                                 See geoips.image_utils.maps.set_boundaries_info_dict
                                     for required fields and defaults
        gridlines_info (dict) : Dictionary of parameters for plotting gridlines.
                                If a field is not included in the dictionary, the default is used for that field.
                                 See geoips.image_utils.maps.set_gridlines_info_dict
                                     for required fields and defaults
    Returns:
        No return values. Overlays are plotted directly on the mapobj and ax instances.

    '''

    from geoips.image_utils.maps import set_boundaries_info_dict, set_gridlines_info_dict
    use_boundaries_info = set_boundaries_info_dict(boundaries_info)
    use_gridlines_info = set_gridlines_info_dict(gridlines_info, area_def)

    from geoips.image_utils.maps import draw_boundaries
    draw_boundaries(mapobj, curr_ax, use_boundaries_info, zorder=boundaries_zorder)

    from geoips.image_utils.maps import draw_gridlines
    draw_gridlines(mapobj, area_def, curr_ax, use_gridlines_info, zorder=gridlines_zorder)


def save_image(fig, out_fname, is_final=True, image_datetime=None, remove_duplicate_minrange=None, savefig_kwargs=None):
    ''' Save the image specified by the matplotlib figure "fig" to the filename out_fname.

    Args:
        fig (Figure) : matplotlib.figure.Figure object that needs to be written to a file.
        out_fname (str) : string specifying the full path to the output filename
        is_final (bool) : Default True. Final imagery must set_axis_on for all axes. Non-final imagery must be
                                        transparent with set_axis_off for all axes, and no pad inches.

    Returns:
        No return values (image is written to disk and IMAGESUCCESS is written to log file)
    '''
    import matplotlib
    import matplotlib.pyplot as plt
    matplotlib.use('agg')
    rc_params = matplotlib.rcParams
    from os.path import dirname, exists as pathexists
    from geoips.filenames.base_paths import make_dirs

    if savefig_kwargs is None:
        savefig_kwargs = {}

    if is_final:
        if not pathexists(dirname(out_fname)):
            make_dirs(dirname(out_fname))
        for ax in fig.axes:
            LOG.info('Adding ax to %s', ax)
            ax.set_axis_on()
        # final with titles, labels, etc.  Note bbox_inches='tight' removes white space, pad_inches=0.1 puts back in
        # a bit of white space.
        LOG.info('Writing %s', out_fname)
        fig.savefig(out_fname, dpi=rc_params['figure.dpi'], pad_inches=0.1, bbox_inches='tight', transparent=False)
        if remove_duplicate_minrange is not None:
            remove_duplicates(out_fname, remove_duplicate_minrange)
    else:
        # Get rid of the colorbar axis for non-final imagery
        if not pathexists(dirname(out_fname)):
            make_dirs(dirname(out_fname))
        # no annotations
        # frameon=False makes it have no titles / lat/lons. does not avoid colorbar, since that is its own ax 
        for ax in fig.axes:
            LOG.info('Removing ax from %s', ax)
            ax.set_axis_off()
        LOG.info('Writing %s', out_fname)
        fig.savefig(out_fname, dpi=rc_params['figure.dpi'], pad_inches=0.0,
                    transparent=True, frameon=False, **savefig_kwargs)
        if remove_duplicate_minrange is not None:
            remove_duplicates(out_fname, remove_duplicate_minrange)

    LOG.info('IMAGESUCCESS wrote %s', out_fname)
    if image_datetime is not None:
        from datetime import datetime
        LOG.info('LATENCY %s %s', datetime.utcnow() - image_datetime, out_fname)
    return [out_fname]


def remove_duplicates(fname, min_range):
    pass


def get_title_string_from_objects(area_def, xarray_obj, product_name_title, product_datatype_title=None,
                                  bg_xarray=None, bg_product_name_title=None, bg_datatype_title=None,
                                  title_copyright=None, title_format=None):

    if title_copyright is None:
        title_copyright = gpaths['GEOIPS_COPYRIGHT']

    from geoips.sector_utils.utils import is_sector_type
    from geoips.dev.title import get_title

    if product_datatype_title is None:
        product_source_name = xarray_obj.source_name
        product_platform_name = xarray_obj.platform_name
        if 'model' in product_name_title:
            try:
                product_source_name = xarray_obj.model_source
                product_platform_name = ''
            except AttributeError:
                LOG.info('No model source in xarray')
        product_datatype_title = '{0} {1}'.format(product_platform_name.upper(), product_source_name.upper())

    if bg_xarray is not None and bg_datatype_title is None:
        bg_datatype_title = '{0} {1}'.format(bg_xarray.platform_name.upper(), bg_xarray.source_name.upper())

    if title_format is not None:
        title_string = get_title(title_format)(area_def, xarray_obj, product_name_title,
                                               product_datatype_title=product_datatype_title,
                                               bg_xarray=bg_xarray,
                                               bg_product_name_title=bg_product_name_title,
                                               bg_datatype_title=bg_datatype_title,
                                               title_copyright=title_copyright)
    elif is_sector_type(area_def, 'tc'):
        title_string = get_title('tc_standard')(area_def, xarray_obj, product_name_title,
                                                product_datatype_title=product_datatype_title,
                                                bg_xarray=bg_xarray,
                                                bg_product_name_title=bg_product_name_title,
                                                bg_datatype_title=bg_datatype_title,
                                                title_copyright=title_copyright)
    else:
        title_string = get_title('static_standard')(area_def, xarray_obj, product_name_title,
                                                    product_datatype_title=product_datatype_title,
                                                    bg_xarray=bg_xarray,
                                                    bg_product_name_title=bg_product_name_title,
                                                    bg_datatype_title=bg_datatype_title,
                                                    title_copyright=title_copyright)
    return title_string


def plot_image(main_ax, data, mapobj, mpl_colors_info, zorder=None):
    ''' Plot the "data" array and map in the matplotlib "main_ax"

        Args:
            main_ax (Axes) : matplotlib Axes object for plotting data and overlays 
            data (numpy.ndarray) : Numpy array of data to plot
            mapobj (Map Object) : Basemap or Cartopy CRS instance 
            mpl_colors_info (dict) Specifies matplotlib Colors parameters for use in both plotting and colorbar
                                   See geoips.image_utils.mpl_utils.create_colorbar for field descriptions.
       Returns:
            No return values
    '''
    # main_ax.set_aspect('auto')

    LOG.info('imshow')
    import numpy
    from geoips.image_utils.maps import is_crs
    if is_crs(mapobj):
        import matplotlib.pyplot as plt
        # Apparently cartopy handles the flipud

        # NOTE passing zorder=None is NOT the same as not passing zorder.
        # Ensure if zorder is passed, it is propagated to imshow.
        extra_args = {}
        if zorder is not None:
            extra_args = {'zorder': zorder}
        main_ax.imshow(data,
                       transform=mapobj,
                       extent=mapobj.bounds,
                       cmap=mpl_colors_info['cmap'],
                       norm=mpl_colors_info['norm'],
                       **extra_args)
    else:
        mapobj.imshow(numpy.flipud(data),
                      ax=main_ax,
                      cmap=mpl_colors_info['cmap'],
                      norm=mpl_colors_info['norm'],
                      aspect='auto')

    return mapobj


def create_figure_and_main_ax_and_mapobj(x_size, y_size, area_def,
                                         font_size=None, existing_mapobj=None, noborder=False):
    ''' Create a figure of x pixels horizontally and y pixels vertically. Use information from matplotlib.rcParams
        xsize = (float(x_size)/dpi)/(right_margin - left_margin)
        ysize = (float(y_size)/dpi)/(top_margin - bottom_margin)
        fig = plt.figure(figsize=[xsize, ysize])
        Parameters:
            x_size (int): number pixels horizontally
            y_size (int): number pixels vertically
            area_def (AreaDefinition) : pyresample AreaDefinition object - used for
                                        initializing map object (basemap or cartopy)
            existing_mapobj (CRS or basemap) : Default None: If specified, do not regenerate mapobj. If None, create
                                                             CRS or basemap object from specified area_def.
            noborder (bool) : Default False: If true, use [0, 0, 1, 1] for axes (allowing for image exact shape of
                                             sector).
        Return:
            (matplotlib.figure.Figure, matplotlib.axes._axes.Axes, mapobject)
                matplotlib Figure object to subsequently use for plotting imagery / colorbars / etc
                matplotlib Axes object corresponding to the single main plotting area.
                cartopy crs or Basemap object for plotting
    '''

    import matplotlib
    matplotlib.use('agg')
    rc_params = matplotlib.rcParams
    import matplotlib.pyplot as plt

    set_fonts(y_size, font_size=font_size)

    # Gather needed rcParam constants
    dpi = rc_params['figure.dpi']

    # I can't seem to get a clean image with no border unless the ax fills the whole figure.
    # Titles / labels don't show up unless we use figure.subplot rc_params
    # It does not appear to be possible to plot the image only once for both the clean and annotated image.
    if noborder:
        left_margin = 0.0
        right_margin = 1.0
        bottom_margin = 0.0
        top_margin = 1.0
    else:
        left_margin = rc_params['figure.subplot.left']   # Fractional distance from left edge of figure for subplot
        right_margin = rc_params['figure.subplot.right']  # Fractional distance from right edge of figure for subplot
        bottom_margin = rc_params['figure.subplot.bottom']  # Fractional distance from bottom edge of figure for subplot
        top_margin = rc_params['figure.subplot.top']     # Fractional distance from top edge of figure for subplot

    xsize = (float(x_size)/dpi)/(right_margin - left_margin)
    ysize = (float(y_size)/dpi)/(top_margin - bottom_margin)

    if existing_mapobj is None:
        LOG.info('creating mapobj instance')
        from geoips.image_utils.maps import area_def2mapobj
        mapobj = area_def2mapobj(area_def)
    else:
        LOG.info('mapobj already exists, not recreating')
        mapobj = existing_mapobj

    LOG.info('Creating figure: left, right, bottom, top, xsize, ysize %s %s %s %s %s %s',
             left_margin, right_margin, bottom_margin, top_margin, xsize, ysize)

    from geoips.image_utils.maps import is_crs
    if is_crs(mapobj):
        # frameon=False creates transparent titles with cartopy
        fig = plt.figure()
    else:
        fig = plt.figure(frameon=False)
    fig.set_size_inches(xsize, ysize)
    set_fonts(y_size, font_size=font_size)

    LOG.info('Creating main ax: left, bottom, width, height %s %s %s %s',
             left_margin, bottom_margin, right_margin - left_margin, top_margin - bottom_margin)

    # cartopy figure with non-transparent titles
    # In [71]: fig = plt.figure()
    # In [72]: main_ax = fig.add_axes([0, 0, 1, 1], projection=mapobj, frame_on=True)
    # In [73]: plt.imshow(plot_data, transform=mapobj, extent=mapobj.bounds)
    # Out[73]: <matplotlib.image.AxesImage at 0x7fcfe5f75eb0>
    # In [74]: main_ax.set_title('Hello', y=1.2, fontsize=20)
    # Out[74]: Text(0.5, 1.2, 'Hello')
    # In [75]: fig.savefig('test.png', transparent=False)

    if is_crs(mapobj):
        # Transparent behind titles without frame_on True
        main_ax = fig.add_axes([left_margin,
                                bottom_margin,
                                right_margin - left_margin,
                                top_margin - bottom_margin],
	    						projection=mapobj,
                                frame_on=not noborder,
                               )
    else:
        main_ax = plt.Axes(fig, [left_margin, bottom_margin, right_margin-left_margin, top_margin-bottom_margin])
    main_ax.set_axis_off()
    fig.add_axes(main_ax)

    return fig, main_ax, mapobj


def set_fonts(figure_y_size, font_size=None):
    ''' Set the fonts in the matplotlib.rcParams dictionary, using matplotlib.rc
        Parameters:
            figure_y_size (int): Font size set relative to number of pixels in the y direction
        No return values
    '''
    import matplotlib
    matplotlib.use('agg')
    mplrc = matplotlib.rc

    # Update font size based on number of lines
    if font_size is not None:
        title_fsize = font_size
    elif int(figure_y_size)/1000 != 0:
        title_fsize = 20*int(figure_y_size)/1000
    else:
        title_fsize = 20

    font = {'family': 'sans-serif',
            'weight': 'bold',
            'size': title_fsize}

    LOG.info('Setting font size to %s for figure_y_size %s', title_fsize, figure_y_size)
    mplrc('font', **font)


def set_title(ax, title_string, figure_y_size, xpos=None, ypos=None, fontsize=None):
    ''' Set the title on figure axis "ax" to string "title_string" 
        Parameters:
            ax (Axes): matplotlib.axes._axes.Axes object to add the title
            title_string (str): string specifying title to attach to axis "ax"
            figure_y_size (int): vertical size of the image, used to proportionally set the title size
        No returns
    '''
    import matplotlib
    matplotlib.use('agg')
    rc_params = matplotlib.rcParams

    # Provide pad room between characters
    fontspace = rc_params['font.size']
    title_line_space = float(fontspace) / figure_y_size
    # num_title_lines = len(title_string.split('\n'))

    if xpos is None:
        xpos = 0.5          # This centers the title
    if ypos is None:
        # ypos = 1 + title_line_space*2
        ypos = 1 + title_line_space*2 # This is relative to main_ax, so greater than 1.
    LOG.info('Setting title: font size %s, xpos %s ypos %s, title_line_space %s',
             fontspace, xpos, ypos, title_line_space)
    LOG.info('    Title string: %s', title_string)

    # from cartopy.mpl.geoaxes import GeoAxes # isinstance(ax, GeoAxes)
    # Slightly more space between title and lon labels
    # ax.set_title(title_string, y=ypos, fontsize=fontsize)
    ax.set_title(title_string, position=[xpos, ypos], fontsize=fontsize)


def create_colorbar(fig, mpl_colors_info):
    '''Routine to create a single colorbar with specified matplotlib ColorbarBase parameters
       cbar_ax = fig.add_axes([<cbar_start_pos>, <cbar_bottom_pos>, <cbar_width>, <cbar_height>])
       cbar = matplotlib.colorbar.ColorbarBase(cbar_ax, cmap=mpl_cmap, extend='both', orientation='horizontal',
                                               norm=cmap_norm, ticks=cmap_ticks, boundaries=cmap_boundaries,
                                               spacing=cmap_spacing)
       cbar.set_label(cbar_label, size=fontsize)

        Parameters:
            fig (Figure): matplotlib.figure.Figure object to attach the colorbar - the colorbar will create its own ax
            mpl_colors_info (dict) : Dictionary of matplotlib Color information, required fields below
                mpl_colors_info['cmap'] (Colormap): matplotlib.colors.Colormap object (LinearSegmentedColormap, etc)
                                                    - this is used to plot the image and to generated the colorbar
                mpl_colors_info['norm'] (Normalize): matplotlib.colors.Normalize object (BoundaryNorm, Normalize, etc)
                                                    - again, this should be used to plot the data also
                mpl_colors_info['cbar_ticks'] (list): list of floats - values requiring tick marks on the colorbar
                mpl_colors_info['cbar_tick_labels'] (list): list of values to use to label tick marks, if other than
                                                            found in cmap_ticks
                mpl_colors_info['boundaries'] (list): if cmap_norm is BoundaryNorm, list of boundaries for discrete
                                                      colors
                mpl_colors_info['cbar_spacing (string): DEFAULT 'proportional', 'uniform' or 'proportional'
                mpl_colors_info['cbar_label (string): string label for colorbar
                mpl_colors_info['colorbar']: (bool) True if a colorbar should be included in the image, False if no cbar
        Returns:
            (matplotlib.colorbar.ColorbarBase): This will have all the pertinent information for ensuring plot and
                                                colorbar use the same parameters
    '''
    cmap_ticklabels = mpl_colors_info['cbar_tick_labels']
    cmap_ticks = mpl_colors_info['cbar_ticks']
    cmap_norm = mpl_colors_info['norm']
    mpl_cmap = mpl_colors_info['cmap']
    cmap_boundaries = mpl_colors_info['boundaries']
    cmap_spacing = mpl_colors_info['cbar_spacing']
    cbar_label = mpl_colors_info['cbar_label']
    if not cmap_ticklabels:
        cmap_ticklabels = cmap_ticks
    import matplotlib
    rc_params = matplotlib.rcParams
    left_margin = rc_params['figure.subplot.left']    # Fractional distance from left edge of figure for subplot
    right_margin = rc_params['figure.subplot.right']    # Fractional distance from left edge of figure for subplot
    fontsize = rc_params['font.size']

    cbar_start_pos = 2*left_margin
    if 'cbar_full_width' in mpl_colors_info and mpl_colors_info['cbar_full_width'] is True:
        cbar_start_pos = left_margin  # Full width colorbar

    cbar_bottom_pos = 0.05
    cbar_height = 0.020

    cbar_width = 1 - 4*left_margin
    if 'cbar_full_width' in mpl_colors_info and mpl_colors_info['cbar_full_width'] is True:
        cbar_width = right_margin - left_margin  # Full width colorbar

    cbar_labelsize = 'small'
    # [left, bottom, width, height]
    cbar_ax = fig.add_axes([cbar_start_pos, cbar_bottom_pos, cbar_width, cbar_height])
    cbar = matplotlib.colorbar.ColorbarBase(cbar_ax, cmap=mpl_cmap, extend='both', orientation='horizontal',
                                            norm=cmap_norm, ticks=cmap_ticks, boundaries=cmap_boundaries,
                                            spacing=cmap_spacing)
    cbar.set_ticklabels(cmap_ticklabels)
    cbar.ax.tick_params(labelsize=cbar_labelsize)
    if cbar_label:
        cbar.set_label(cbar_label, size=fontsize)
    return cbar
