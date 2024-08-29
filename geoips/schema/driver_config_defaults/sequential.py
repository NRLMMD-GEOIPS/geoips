from typing import Literal, Union, Dict, List

from pydantic import BaseModel


class Matching(BaseModel, extra="allow"):
    """Default schema for the 'matching' attribute of RequiredFiles."""

    file_format: str
    band_resolution_mapping: Dict[str]
    segment_divisions: List[str]


class RequiredFiles(BaseModel, extra="allow"):
    """Default schema for 'required_files' attribute.

    This is a required attribute of the DriverConfigDefaults schema, which is applied to
    all DriverConfigDefaults plugins.
    """

    default: Literal["single", "set"]
    matching: Union[Matching, None]


class Sequential(BaseModel, extra="allow"):
    """Default schema for the sequential-based driver_config_defaults plugin."""

    watchdir: str
    template: str
    date_format: Literal["calendar", "julian"]
    sectors: List[str]
    output_types: List[str]
    required_files: RequiredFiles
