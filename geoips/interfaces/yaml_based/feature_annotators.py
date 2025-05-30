# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Feature Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface
from geoips.pydantic.feature_annotators import FeatureAnnotatorPluginModel


class FeatureAnnotatorsInterface(BaseYamlInterface):
    """Interface for feature annotator plugins."""

    name = "feature_annotators"
    validator = FeatureAnnotatorPluginModel


feature_annotators = FeatureAnnotatorsInterface()
