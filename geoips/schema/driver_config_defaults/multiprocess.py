from typing import Literal

from pydantic import Field
from typing_extensions import Annotated

from geoips.schema.driver_config_defaults.sequential import Sequential


class Multiprocess(Sequential, extra="strict"):
    """Default schema for multiprocess-based driver_config_defaults plugin."""

    core_count: Annotated[int, Field(strict=True, gt=0)]
    processing_type: Literal["Pool", "Process", "Queue"]
