# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 output-formatter plugins."""

# Third-Party Libraries
from pydantic import Field
from pyresample.geometry import AreaDefinition

# GeoIPS imports
from geoips.pydantic_models.v1.bases import FrozenModel, PermissiveFrozenModel

PLUGIN_PROVIDED = "plugin_provided"
class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Output-Formatter step argument definition.

    Pydantic model defining and validating Output Formatter step arguments.
    """

    append: bool = Field(False)
    basedir: str = Field(PLUGIN_PROVIDED)

    # area_def: AreaDefinition = Field(
    #     description="pyresample AreaDefinition object specifying the area covered by the current plot"
    # )


    # # not single source, possibly config-based
    # bg_data = Field(None)
    # bg_mpl_colors_info = Field(None)
    # bg_xarray = Field(None)
    # bg_datatype_title: str | None = Field(None, description="background data type")
    # bg_product_name_title: str | None = Field(
    #     None, description="background product title"
    # )
    # clean_fname = Field(None)
    # # --output_formatter_kwargs
    # clobber: bool = Field(False)
    # cog: bool = Field(True)
    # #  TBD
    # # compression_kwargs=None
    # existing_image: str = Field(None)
    # fig = Field(None)
    # # --output_formatter_kwargs 
    # hist_colorbar: bool = Field(False)
    # is_3d: bool = Field(False)
    # main_ax = Field(None)
    # mapobj = Field(None)
    # metadata_dir: str = Field(
    #     "metadata",
    #     description="Subdirectory name for metadata; using non-default allows for non-operational outputs",
    # )
    # metadata_fname_dict = Field(None)
    # mpl_colors_info: str = Field(None)
    # output_dict = Field(
    #     None,
    # )
    # output_fname_dict = Field(None)
    # overwrite: bool = Field(True)
    # pressure_range_dict = Field(None)
    # product_name_title: str = Field(None)
    # product_datatype_title: str = Field(None)
    # remove_duplicate_minrange = Field(None)
    # # of: unprojected_image
    # savefig_kwargs: dict = Field(None)
    # # of: test_winds
    # # source_names

    # title_copyright: str | None = Field(None, description="string for copyright")
    # title_formatter: str | None = Field(None, description="format for title")
    # use_compression: bool = Field(False)
    # var_name = Field(
    #     None,
    # )
    # # of: test_winds
    # # varlist
    # working_directory: str = Field(PLUGIN_PROVIDED)
    # # --output_formatter_kwargs
    # x_size = Field(None)
    # # --output_formatter_kwargs
    # y_size = Field(None)
