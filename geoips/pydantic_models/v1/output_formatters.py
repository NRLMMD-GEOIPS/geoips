# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 output-formatter plugins."""

# cspell:ignore TCWW
# cspel

# Python Standard Library
from typing import Any

# Third-Party Libraries
from pydantic import Field
from pyresample.geometry import AreaDefinition

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel

PLUGIN_PROVIDED = "plugin_provided"


class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Output-Formatter step argument definition.

    Pydantic model defining and validating Output Formatter step arguments.
    """

    append: bool = Field(
        False,
        description=(
            "When True, open the output file in append mode ('a') instead of write mode"
            "('w'). Automatically forced to True for every dataset beyond the first"
            "when multiple datasets are written to the same output file."
        ),
    )
    area_def: AreaDefinition | None = Field(
        None, description="The domain over which to read data."
    )
    # TASK: validate this to drop after the 2026 GeoIPS workshop
    basedir: str = Field(
        PLUGIN_PROVIDED,
        description=(
            "Used to construct relative product paths in metadata output. Originally"
            " used to strip the TCWWW root path before replacing it with a public URL;"
            " now superseded by replace_geoips_paths() and no longer used across the"
            " entire implementation."
        ),
    )
    # used to render to background image
    # assign the bg_data dataset from the DataTree
    bg_data: Any | None = Field(None)
    bg_datatype_title: str | None = Field(None, description="background data type")
    bg_mpl_colors_info: dict[str, Any] | None = Field(
        None,
        description=("Matplotlib colormap configuration for the background dataset"),
    )
    bg_product_name_title: str | None = Field(
        None, description="Title of background product"
    )
    # used for constructing the title string to extract platform
    # do not remove this until after the 2026 GeoIPS workshop
    bg_xarray: Any | None = Field(None)
    # TASK: validate this to drop after the 2026 GeoIPS workshop
    cog: bool = Field(
        True,
        description=(
            "Whether to produce a Cloud-Optimized GeoTIFF with internal overview"
            " levels. Currently this has no effect as overview generation is handled"
            " automatically by cog_translate() call."
        ),
    )
    clean_fname: str | None = Field(
        None,
        description=(
            "Output file path for a overlay-free elements such as no background"
            " imagery, coastlines, gridlines, title, or colorbar. When None, the clean"
            " image is skipped."
        ),
    )
    clobber: bool = Field(
        default=False,
        description="whether to overwrite the output file even if it exists",
    )
    # dead argument all output_formatters where used
    # TASK: validate this to drop after the 2026 GeoIPS workshop 
    existing_image: str | None = Field(
        None,
        description=(
            "File path to a pre-rendered image onto which new data would be composited"
        ),
    )
    is_3d: bool = Field(
        False,
        description=(
            "When True, interpret the product data as a 3D array; otherwise,"
            "interpret it as a 2D array"
        ),
    )
    title_copyright: str | None = Field(None, description="copyright string")
    x_size: int = Field(
        None,
        description=(
            "Number of pixels in the x direction of the projected area definition"
        ),
    )
    y_size: int = Field(
        None,
        description=(
            "Number of pixels in the y direction of the projected area definition"
        ),
    )
    title_formatter: str | None = Field(None, description="format for title")

    fig: Any | None = Field(None)
    hist_colorbar: bool = Field(False)
    main_ax: Any | None = Field(None)
    mapobj: Any | None = Field(None)
    metadata_dir: str = Field(
        "metadata",
        description=(
            "Subdirectory name for metadata; using non-default allows for"
            " non-operational outputs"
        ),
    )
    metadata_fname_dict: dict | None = Field(None)
    mpl_colors_info: Any | None = Field(None)
    output_dict: dict | None = Field(None)
    output_fname_dict: dict | None = Field(None)
    overwrite: bool = Field(True)
    pressure_range_dict: dict | None = Field(None)
    product_name_title: str | None = Field(None)
    product_datatype_title: str | None = Field(None)
    remove_duplicate_minrange: Any | None = Field(None)
    savefig_kwargs: dict | None = Field(None)
    use_compression: bool = Field(False)
    var_name: str | None = Field(None)
    working_directory: str = Field(PLUGIN_PROVIDED)
