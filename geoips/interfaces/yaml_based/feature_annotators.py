# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Feature Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface
from geoips.pydantic_models.v1.feature_annotators import FeatureAnnotatorPluginModel


class FeatureAnnotatorsInterface(BaseYamlInterface):
    """Interface for feature annotator plugins."""

    name = "feature_annotators"
    validator = FeatureAnnotatorPluginModel
    # use_pydantic = True


feature_annotators = FeatureAnnotatorsInterface()
