from typing import Union

from pydantic import Field
from typing_extensions import Annotated

from geoips.schema.driver_config_defaults.sequential import Sequential


class Multiprocess(Sequential, extra="strict"):
    """Default schema for slurm-based driver_config_defaults plugin."""

    mem_per_cpu: Union[Annotated[float, Field(strict=True, gt=0)], None]
    ntasks: Union[Annotated[int, Field(strict=True, gt=0)], None]
    partition: Union[str, None]
