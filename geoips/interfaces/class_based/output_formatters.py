# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters interface class."""

import logging
from os.path import dirname, exists

import cartopy.crs as crs
import numpy

from geoips.filenames.base_paths import make_dirs
from geoips.geoips_utils import replace_geoips_paths
from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface
from geoips.image_utils.mpl_utils import (
    create_figure_and_main_ax_and_mapobj,
    save_image,
)

LOG = logging.getLogger(__name__)


class BaseOutputFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS output_formatter plugins."""

    def write_xarray_netcdf(
        self,
        xarray_obj,
        ncdf_fname,
        clobber=False,
        use_compression=True,
        compression_kwargs=None,
    ):
        """Write out xarray_obj to netcdf file named ncdf_fname."""

        make_dirs(dirname(ncdf_fname))

        orig_attrs = xarray_obj.attrs.copy()
        orig_var_attrs = {}

        # Specially handled attributes.
        area_def_str = "none"
        # GEOIPS 1 COMPATIBILITY
        if "area_def" in xarray_obj.attrs.keys():
            # Must pop off the actual area_defintion - does not write to xarray properly
            area_def = xarray_obj.attrs.pop("area_def")
            area_def_str = repr(area_def)
            xarray_obj.attrs["area_def_str"] = area_def_str
        # If actual area_definition object, write it out to xarray as str
        elif "area_definition" in xarray_obj.attrs.keys():
            # If area_definition_str was explicitly defined on the area_definition
            # object, use that
            if hasattr(xarray_obj.area_definition, "area_definition_str"):
                # Must pop off the actual area_defintion - does not write to xarray
                # properly
                area_def_str = xarray_obj.area_definition.area_definition_str
                area_def = xarray_obj.attrs.pop("area_definition")
                xarray_obj.attrs["area_definition_str"] = area_def_str
            else:
                # Must pop off the actual area_defintion - does not write to xarray
                # properly
                area_def = xarray_obj.attrs.pop("area_definition")
                area_def_str = repr(area_def)
                xarray_obj.attrs["area_definition_str"] = area_def_str

        # Standard attribute cleaning for proper serialization for xarray.to_netcdf.
        for attr in xarray_obj.attrs.copy().keys():
            self.clean_attr_for_netcdf(xarray_obj, attr)
        for varname in xarray_obj.variables.keys():
            orig_var_attrs[varname] = xarray_obj[varname].attrs.copy()
            for attr in xarray_obj[varname].attrs.keys():
                self.clean_attr_for_netcdf(xarray_obj[varname], attr)

        # Strings to print to the log statement, not used in any other way.
        # If an attribute is not defined, print 'none'.
        roi_str = "none"
        if "interpolation_radius_of_influence" in xarray_obj.attrs.keys():
            roi_str = xarray_obj.interpolation_radius_of_influence

        sdt_str = "none"
        if "start_datetime" in xarray_obj.attrs.keys():
            sdt_str = xarray_obj.attrs["start_datetime"]

        edt_str = "none"
        if "end_datetime" in xarray_obj.attrs.keys():
            edt_str = xarray_obj.attrs["end_datetime"]

        dp_str = "none"
        if "data_provider" in xarray_obj.attrs.keys():
            dp_str = xarray_obj.attrs["data_provider"]

        LOG.info(
            "Writing xarray obj to file %s, source %s, platform %s, start_dt %s, ",
            "end_dt %s, %s %s, %s %s, %s %s",
            ncdf_fname,
            xarray_obj.source_name,
            xarray_obj.platform_name,
            sdt_str,
            edt_str,
            "provider",
            dp_str,
            "roi",
            roi_str,
            "area_def",
            area_def_str,
        )

        if use_compression:
            if compression_kwargs is None:
                compression_kwargs = {"zlib": True, "complevel": 5}
            encoding = {x: compression_kwargs for x in list(xarray_obj)}
        else:
            encoding = {}

        # Only re-write the file if requested.
        if clobber is True or not exists(ncdf_fname):
            xarray_obj.to_netcdf(ncdf_fname, encoding=encoding)
        else:
            LOG.warning("SKIPPING not outputing file %s, exists", ncdf_fname)

        # Put the original attributes back at both the dataset level and the variable
        # level. We do not want the serializable attributes on the original dataset.
        xarray_obj.attrs = orig_attrs
        for varname in xarray_obj.variables.keys():
            xarray_obj[varname].attrs = orig_var_attrs[varname]

        return [ncdf_fname]

    def output_clean_windbarbs(
        self,
        area_def,
        clean_fnames,
        mpl_colors_info,
        image_datetime,
        formatted_data_dict,
        fig=None,
        main_ax=None,
        mapobj=None,
        barb_color_variable="speed",
    ):
        """Plot and save "clean" windbarb imagery.

        No background imagery, coastlines, gridlines, titles, etc.

        Returns
        -------
        list of str
            Full paths to all resulting output files.
        """
        LOG.info("Starting clean_fname")
        if fig is None and main_ax is None and mapobj is None:
            # Create matplotlib figure and main axis, where the main image will be
            # plotted
            fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
                area_def.width, area_def.height, area_def, noborder=True
            )

        self.plot_barbs(
            main_ax,
            mapobj,
            mpl_colors_info,
            formatted_data_dict,
            barb_color_variable=barb_color_variable,
        )

        success_outputs = []

        if clean_fnames is not None:
            for clean_fname in clean_fnames:
                success_outputs += save_image(
                    fig, clean_fname, is_final=False, image_datetime=image_datetime
                )

        return success_outputs

    def format_windbarb_data(self, xarray_obj, product_name):
        """Format windbarb data before plotting."""
        # lat=xarray_obj['latitude'].to_masked_array()
        # lon2=xarray_obj['longitude'].to_masked_array()
        # direction=xarray_obj['wind_dir_deg_met'].to_masked_array()
        # speed=xarray_obj['wind_speed_kts'].to_masked_array()

        # u=speed * numpy.sin((direction+180)*3.1415926/180.0)
        # v=speed * numpy.cos((direction+180)*3.1415926/180.0)

        # u=speed * numpy.sin(direction*3.1415926/180.0)
        # v=speed * numpy.cos(direction*3.1415926/180.0)

        data_cols = xarray_obj[product_name].attrs.get(
            "windbarb_data_columns", ["speed", "direction", "rain_flag"]
        )

        num_product_arrays = 1
        if len(xarray_obj[product_name].shape) == 3:
            num_product_arrays = xarray_obj[product_name].shape[2]

        # This is 2-D, with only one array per variable (speed, direction,
        # rain_flag) - meaning NO ambiguities
        if len(xarray_obj[product_name].shape) == 3 and num_product_arrays == 3:
            speed = xarray_obj[product_name].to_masked_array()[:, :, 0]
            direction = xarray_obj[product_name].to_masked_array()[:, :, 1]
            rain_flag = xarray_obj[product_name].to_masked_array()[:, :, 2]
        # This is 2-D, with FOUR arrays per variable (speed, direction, rain_flag)
        # - meaning 4 ambiguities
        elif len(xarray_obj[product_name].shape) == 3 and num_product_arrays == 12:
            speed = xarray_obj[product_name].to_masked_array()[:, :, 0:4]
            direction = xarray_obj[product_name].to_masked_array()[:, :, 4:8]
            rain_flag = xarray_obj[product_name].to_masked_array()[:, :, 8:12]
        # This is 1-D, with one vector per variable - no ambiguities.
        elif xarray_obj[product_name].ndim == 3:
            speed = xarray_obj[product_name].to_masked_array()[:, :, 0]
            direction = xarray_obj[product_name].to_masked_array()[:, :, 1]
            rain_flag = xarray_obj[product_name].to_masked_array()[:, :, 2]
            if "pressure" in data_cols:
                pressure = xarray_obj[product_name].to_masked_array()[:, :, 3]
        else:
            speed = xarray_obj[product_name].to_masked_array()[:, 0]
            direction = xarray_obj[product_name].to_masked_array()[:, 1]
            rain_flag = xarray_obj[product_name].to_masked_array()[:, 2]
            if "pressure" in data_cols:
                pressure = xarray_obj[product_name].to_masked_array()[:, 3]
        # These should probably be specified in the product dictionary.
        # It will vary per-sensor / data type, these basically only currently work with
        # ASCAT 25 km data.
        # This would also avoid having the product names hard coded in the output
        # module code.

        from geoips.interfaces import products

        source_prod_spec = products.get_plugin(xarray_obj.source_name, product_name)
        prod_plugin = xarray_obj.attrs.get("product_plugin", source_prod_spec)

        try:
            barb_args = prod_plugin["spec"]["windbarb_plotter"]["plugin"]["arguments"]
        except KeyError:
            barb_args = {}

        if barb_args:
            # Thinning the data points to better display the windbards
            thinning = barb_args["thinning"]
            barblength = barb_args["length"]
            linewidth = barb_args["width"]
            sizes_dict = barb_args["sizes_dict"]
            rain_size = barb_args["rain_size"]
        elif product_name == "windbarbs":
            # Thinning the data points to better display the windbards
            thinning = 1  # skip data points
            barblength = 5.0
            linewidth = 1.5
            sizes_dict = dict(height=0.7, spacing=0.3)
            rain_size = 10
        elif product_name == "wind-ambiguities" or "wind-ambiguities" in product_name:
            # Thinning the data points to better display the windbards
            thinning = 1  # skip data points
            barblength = 5  # Length of individual barbs
            linewidth = 2  # Width of individual barbs
            rain_size = 10  # Marker size for rain_flag
            sizes_dict = dict(
                height=0,
                spacing=0,
                width=0,  # flag width, relative to barblength
                emptybarb=0.5,
            )
        else:
            raise ValueError(f"Unknown product {product_name}")

        lat = xarray_obj["latitude"].to_masked_array()
        lon2 = xarray_obj["longitude"].to_masked_array()
        u = speed * numpy.sin((direction + 180) * 3.1415926 / 180.0)
        v = speed * numpy.cos((direction + 180) * 3.1415926 / 180.0)

        # convert longitudes to (-180,180)
        # lon=utils.wrap_longitudes(lon2)
        # Must be 0-360 for barbs
        lon = numpy.ma.where(lon2 < 0, lon2 + 360, lon2)
        thin_slice = [slice(0, None, thinning)] * lat.ndim

        lat2 = lat[tuple(thin_slice)]
        lon2 = lon[tuple(thin_slice)]
        u2 = u[tuple(thin_slice)]
        v2 = v[tuple(thin_slice)]
        speed2 = speed[tuple(thin_slice)]
        rain_flag2 = rain_flag[tuple(thin_slice)]
        if "pressure" in data_cols:
            pressure2 = pressure[tuple(thin_slice)]

        if lat2.min() > 0:
            flip_barb = False
        elif lat2.max() < 0:
            flip_barb = True
        else:
            flip_barb = numpy.ma.where(lat2 > 0, False, True).data
        good_inds = numpy.ma.where(speed2)
        return_dict = {}
        if len(lon2.shape) != len(speed2.shape):
            return_dict["lon"] = lon2[good_inds[0:2]]
        else:
            return_dict["lon"] = lon2[good_inds]
        if len(lat2.shape) != len(speed2.shape):
            return_dict["lat"] = lat2[good_inds[0:2]]
        else:
            return_dict["lat"] = lat2[good_inds]
        if flip_barb is not True and flip_barb is not False:
            if len(flip_barb.shape) != len(speed2.shape):
                return_dict["flip_barb"] = flip_barb[good_inds[0:2]]
            else:
                return_dict["flip_barb"] = flip_barb[good_inds]
        else:
            return_dict["flip_barb"] = flip_barb
        return_dict["u"] = u2[good_inds]
        return_dict["v"] = v2[good_inds]
        return_dict["speed"] = speed2[good_inds]
        return_dict["rain_inds"] = numpy.ma.where(rain_flag2[good_inds])
        return_dict["barb_length"] = barblength
        return_dict["line_width"] = linewidth
        return_dict["sizes_dict"] = sizes_dict
        return_dict["rain_size"] = rain_size
        if "pressure" in data_cols:
            return_dict["pressure"] = pressure2[good_inds]

        return return_dict

    def assign_height_levels(self, windbarb_data_dict, pressure_range_dict):
        """Assing derived motion winds to specified height levels.

        Using the pressure associated with each retrieved wind observation, assign to
        a specified level (e.g. Low/Mid/High) based on predefined pressure ranges. Each
        pressure level is assigned an integer, and any unassigned are set to 0

        Parameters
        ----------
        formatted_data_dict : dict
            Dictionary holding DMW data - must include a pressure key
        pressure_range_dict : dict
            Dictionary specifying pressure range for each defined level.
            e.g. {"Low": [701, 1013.25], "Mid": [401, 700], "High": [0, 400]}

        Returns
        -------
        tuple
            Array of assigned level numbers, and list of associated labels that can be
            used to set the ticks on a colorbar
        """
        pressure = windbarb_data_dict["pressure"]
        n_valid = numpy.count_nonzero(pressure)
        height_num = numpy.zeros(pressure.shape)
        level_labels = ["Unassigned"]
        for i, (level, pressure_range) in enumerate(pressure_range_dict.items()):
            max_pres = max(pressure_range)
            min_pres = min(pressure_range)
            pressure_mask = (pressure.data >= min_pres) & (pressure.data <= max_pres)
            height_num[pressure_mask] = i + 1
            level_labels.append(f"{level}\n({max_pres} - {min_pres} hPa)")
            LOG.info(
                "Number of wind retrievals for %s: %s",
                level,
                numpy.count_nonzero(pressure_mask),
            )
        LOG.info("Assigned %s/%s retrievals", numpy.count_nonzero(height_num), n_valid)
        return height_num, level_labels

    def plot_barbs(
        self,
        main_ax,
        mapobj,
        mpl_colors_info,
        formatted_data_dict,
        barb_color_variable="speed",
    ):
        """Plot windbarbs on matplotlib figure."""
        # main_ax.extent = area_def.area_extent_ll
        main_ax.set_extent(mapobj.bounds, crs=mapobj)
        # main_ax.extent = mapobj.bounds
        # NOTE this does not work if transform=mapobj.
        # Something about transforming to PlateCarree projection, then
        # reprojecting to mapobj.  I don't fully understand it, but this
        # works beautifully, and transform=mapobj puts all the vectors
        # in the center of the image.
        main_ax.scatter(
            x=formatted_data_dict["lon"].data[formatted_data_dict["rain_inds"]],
            y=formatted_data_dict["lat"].data[formatted_data_dict["rain_inds"]],
            transform=crs.PlateCarree(),
            marker="D",
            color="k",
            s=formatted_data_dict["rain_size"],
            zorder=2,
        )
        main_ax.barbs(
            formatted_data_dict["lon"].data,
            formatted_data_dict["lat"].data,
            formatted_data_dict["u"].data,
            formatted_data_dict["v"].data,
            formatted_data_dict[barb_color_variable].data,
            transform=crs.PlateCarree(),
            pivot="tip",
            rounding=False,
            cmap=mpl_colors_info["cmap"],
            flip_barb=formatted_data_dict["flip_barb"],
            # barb_increments=dict(half=10, full=20, flag=50),
            sizes=formatted_data_dict["sizes_dict"],
            length=formatted_data_dict["barb_length"],
            linewidth=formatted_data_dict["line_width"],
            norm=mpl_colors_info["norm"],
            zorder=1,
        )

    def update_sector_info_with_default_metadata(
        self, area_def, xarray_obj, product_filename=None, metadata_filename=None
    ):
        """Update sector info found in "area_def" with standard metadata output.

        This function is used by metadata_tc output formatter as well for updating the
        sector_info with these additional default metadata fields. We should not filter
        out non-default metadata here, since metadata_tc uses this function.

        Parameters
        ----------
        area_def : AreaDefinition
            Pyresample AreaDefinition of sector information
        xarray_obj : xarray.Dataset
            xarray Dataset object that was used to produce product
        product_filename : str
            Full path to full product filename that this YAML file refers to

        Returns
        -------
        dict
            sector_info dict with standard metadata added
             * bounding box
             * product filename with wildcards
             * basename of original source filenames
        """
        sector_info = area_def.sector_info.copy()

        if hasattr(area_def, "sector_type") and "sector_type" not in sector_info:
            sector_info["sector_type"] = area_def.sector_type

        sector_info["bounding_box"] = {}
        sector_info["bounding_box"]["minlat"] = area_def.area_extent_ll[1]
        sector_info["bounding_box"]["maxlat"] = area_def.area_extent_ll[3]
        sector_info["bounding_box"]["minlon"] = area_def.area_extent_ll[0]
        sector_info["bounding_box"]["maxlon"] = area_def.area_extent_ll[2]
        sector_info["bounding_box"]["pixel_width_m"] = area_def.pixel_size_x
        sector_info["bounding_box"]["pixel_height_m"] = area_def.pixel_size_y
        sector_info["bounding_box"]["image_width"] = area_def.width
        sector_info["bounding_box"]["image_height"] = area_def.height
        sector_info["bounding_box"]["proj4_string"] = area_def.proj_str

        if product_filename:
            sector_info["product_filename"] = replace_geoips_paths(product_filename)
        if metadata_filename:
            sector_info["metadata_filename"] = replace_geoips_paths(metadata_filename)

        if "source_file_names" in xarray_obj.attrs.keys():
            sector_info["source_file_names"] = xarray_obj.source_file_names
        # Backwards compatibility, so the default metadata doesn't change.
        if "source_file_names" in xarray_obj.attrs.keys():
            sector_info["source_file_names"] = xarray_obj.source_file_names

        return sector_info


class OutputFormattersInterface(BaseClassInterface):
    """Data format for the resulting output product (e.g. netCDF, png)."""

    name = "output_formatters"
    plugin_class = BaseOutputFormatterPlugin

    required_args = {
        "image": ["area_def", "xarray_obj", "product_name", "output_fnames"],
        "unprojected": ["xarray_obj", "product_name", "output_fnames"],
        "image_overlay": ["area_def", "xarray_obj", "product_name", "output_fnames"],
        "image_multi": [
            "area_def",
            "xarray_obj",
            "product_names",
            "output_fnames",
            "mpl_colors_info",
        ],
        "xrdict_area_varlist_to_outlist": ["xarray_dict", "area_def", "varlist"],
        "xrdict_area_product_outfnames_to_outlist": [
            "xarray_dict",
            "area_def",
            "product_name",
            "output_fnames",
        ],
        "xrdict_area_product_to_outlist": [
            "xarray_dict",
            "area_def",
            "product_name",
        ],
        "xrdict_to_outlist": [
            "xarray_dict",
        ],
        "xrdict_varlist_outfnames_to_outlist": [
            "xarray_dict",
            "varlist",
            "output_fnames",
        ],
        "xarray_data": ["xarray_obj", "product_names", "output_fnames"],
        "standard_metadata": [
            "area_def",
            "xarray_obj",
            "metadata_yaml_filename",
            "product_filename",
        ],
    }
    required_kwargs = {
        "image": ["product_name_title", "mpl_colors_info", "existing_image"],
        "unprojected": ["product_name_title", "mpl_colors_info"],
        "image_overlay": [
            "product_name_title",
            "clean_fname",
            "mpl_colors_info",
            "clean_fname",
            "feature_annotator",
            "gridline_annotator",
            "clean_fname",
            "product_datatype_title",
            "clean_fname",
            "bg_data",
            "bg_mpl_colors_info",
            "clean_fname",
            "bg_xarray",
            "bg_product_name_title",
            "bg_datatype_title",
            "clean_fname",
            "remove_duplicate_minrange",
        ],
        "image_multi": ["product_name_titles"],
        "xarray_dict_data": ["append", "overwrite"],
        "xarray_dict_to_image": [],
        "xarray_data": [],
        "standard_metadata": ["metadata_dir", "basedir", "output_dict"],
        "xrdict_varlist_outfnames_to_outlist": [],
        "xrdict_area_varlist_to_outlist": [],
        "xrdict_area_product_outfnames_to_outlist": [],
        "xrdict_area_product_to_outlist": [],
        "xrdict_to_outlist": [],
    }


output_formatters = OutputFormattersInterface()
