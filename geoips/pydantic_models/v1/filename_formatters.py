# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 filename-formatter plugins."""

# Python Standard Libraries
from typing import Any

# Third-Party Libraries
from pydantic import Field
from pyresample.geometry import AreaDefinition

# GeoIPS imports
from geoips.constants import PLUGIN_PROVIDED
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class FilenameFormatterArgumentsModel(PermissiveFrozenModel):
    """Filename-Formatter step argument definition.

    Pydantic model defining and validating Filename Formatter step arguments.
    """

    area_def: AreaDefinition | None = Field(
        None, description="Spatial domain to process."
    )
    basedir: str = Field(
        PLUGIN_PROVIDED, description="Full path to base directory of final product"
    )
    coverage: float | None = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Image coverage, float between 0.0 and 100.0",
    )
    extension: str | None = Field(None, description="Extension of filename")
    extra: str | None = Field(
        None,
        description=(
            "String to include in filename 'extra' field" " If None, use fillval of 'x'"
        ),
    )
    metadata_dir: str = Field(
        "metadata", description="Subdirectory for metadata output files."
    )
    metadata_type: str = Field(
        "sector_information",
        description="Type of metadata to include in the output filename.",
    )
    output_dict: dict[str, Any] | None = Field(
        None,
        description=(
            "Additional key-value pairs passed through to the filename formatter."
        ),
    )
    output_type: str = Field(
        PLUGIN_PROVIDED,
        description=(
            "Requested output format (e.g., PNG, JPG, TIFF)."
            "Defaults to the plugin-provided value."
        ),
    )
    output_type_dir: str | None = Field(
        None, description="If None, default to output_type."
    )
    product_filename: str | None = Field(None)
    product_dir: str | None = Field(None)
    product_subdir: str | None = Field(None)
    source_dir: str | None = Field(None)
