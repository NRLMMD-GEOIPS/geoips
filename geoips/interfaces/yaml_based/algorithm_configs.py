# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Algorithm Config interface module."""

from geoips.interfaces.base import BaseYamlInterface


class AlgorithmConfigsInterface(BaseYamlInterface):
    """Interface for algorithm config plugins."""

    name = "algorithm_configs"
    use_pydantic = True
    # validator = FeatureAnnotatorPluginModel


algorithm_configs = AlgorithmConfigsInterface()
