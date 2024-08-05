# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Feature Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface


class FeatureAnnotatorsInterface(BaseYamlInterface):
    """Interface for feature annotator plugins."""

    name = "feature_annotators"


feature_annotators = FeatureAnnotatorsInterface()
