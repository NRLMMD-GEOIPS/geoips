from typing import Any, Dict, Optional
from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from matplotlib.lines import Line2D

from geoips.pydantic import Plugin
from geoips.pydantic.bases import Plugin, LineArgs


class GridlineSpacing(BaseModel):
    latitude: float
    longitude: float


class GridlineAnnotatorSpec(BaseModel):
    """Class to represent the `spec` section of a GridlineAnnotator plugin."""

    spacing: GridlineSpacing
    lines: LineArgs


class GridlineAnnotator(Plugin):
    """Class to represent a GridlineAnnotator plugin."""

    spec: GridlineAnnotatorSpec
