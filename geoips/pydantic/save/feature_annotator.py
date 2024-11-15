from typing import Any, Dict, Optional
from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from matplotlib.lines import Line2D

from geoips.pydantic import Plugin
from geoips.pydantic.bases import Plugin, LineFeatureArgs


class FeatureAnnotatorSpec(BaseModel):
    """Class to represent the `spec` section of a FeatureAnnotator plugin."""

    coastline: FeatureArgs = {"enabled": False}
    borders: FeatureArgs = {"enabled": False}
    rivers: FeatureArgs = {"enabled": False}
    states: FeatureArgs = {"enabled": False}
    # land: ???
    # ocean: ???


class FeatureAnnotator(Plugin):
    """Class to represent a FeatureAnnotator plugin."""

    spec: FeatureAnnotatorSpec
