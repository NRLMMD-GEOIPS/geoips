from geoips.interfaces.base import BaseInterface, BasePlugin


class AlgorithmsInterface(BaseInterface):
    """Data manipulations to apply to the dataset."""
    name = "algorithms"
    deprecated_family_attr = "alg_func_type"


algorithms = AlgorithmsInterface()

