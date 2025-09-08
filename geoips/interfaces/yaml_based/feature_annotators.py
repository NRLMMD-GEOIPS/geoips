# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Feature Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface


class FeatureAnnotatorsInterface(BaseYamlInterface):
    """Interface for feature annotator plugins."""

    name = "feature_annotators"
    use_pydantic = True


feature_annotators = FeatureAnnotatorsInterface()
