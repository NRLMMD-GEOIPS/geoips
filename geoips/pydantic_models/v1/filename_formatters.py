# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 filename-formatter plugins."""

# Third-Party Libraries
from pydantic import Field

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel

PLUGIN_PROVIDED = "plugin_provided"

class FilenameFormatterArgumentsModel(PermissiveFrozenModel):
    """Filename-Formatter step argument definition.

    Pydantic model defining and validating Filename Formatter step arguments.
    """

    area_def:
    basedir: str = Field(PLUGIN_PROVIDED, description="Base directory for output file.")
    coverage: float = Field(
        None, description="Image coverage, float between 0.0 and 100.0"
    )
    extra_field: 
    output_type: str = Field(
        None,
        description=" Requested output format, ie png, jpg, tif, etc, defaults to None",
    )
    output_type_dir: str = Field(None, description="If None, default to output_type.")
    product_dir: str = Field(None)
    product_subdir: str = Field(None)
    source_dir: str = Field(None)
    output_dict: str = Field(None)
    extension: str = Field(None)
