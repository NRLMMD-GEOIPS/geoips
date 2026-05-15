# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pydantic models used to validate GeoIPS OBP v1 filename-formatter plugins."""

# Third-Party Libraries
from pydantic import DirectoryPath, Field

# GeoIPS imports
from geoips.pydantic_models.v1.bases import PermissiveFrozenModel


class FilenameFormatterArgumentsModel(PermissiveFrozenModel):
    """Filename-Formatter step argument definition.

    Pydantic model defining and validating Filename Formatter step arguments.
    """

    # product_names is moved to GlobalVariables
    # coverage should go to GlobalVariables
    coverage: float = Field(
        None, description="Image coverage, float between 0.0 and 100.0"
    )
    output_type: str = Field(
        None,
    )
    # What does default to output_type means here
    output_type_dir: DirectoryPath = Field(
        None, description="If None, default to output_type."
    )
    product_dir: DirectoryPath = Field(None)
    # product_dir isNone then set product_dir = product_name
    # Write a model validator for this
    product_subdir: DirectoryPath = Field(None)
    # if this is None then set
    # source_dir = source_name
    source_dir: DirectoryPath = Field(None)
    basedir: DirectoryPath = Field(None, description="Base directory for output file.")
    output_dict: DirectoryPath = Field(None)
