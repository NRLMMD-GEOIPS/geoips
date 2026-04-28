# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Feature Annotator interface module."""

from geoips.interfaces.base import BaseYamlInterface
from geoips.filenames.base_paths import PATHS as gpaths

# from geoips.pydantic_models.v1.feature_annotators import FeatureAnnotatorPluginModel


class FeatureAnnotatorsInterface(BaseYamlInterface):
    """Interface for feature annotator plugins."""

    name = "feature_annotators"
    use_pydantic = gpaths["GEOIPS_USE_PYDANTIC"]
    # validator = FeatureAnnotatorPluginModel


feature_annotators = FeatureAnnotatorsInterface()
