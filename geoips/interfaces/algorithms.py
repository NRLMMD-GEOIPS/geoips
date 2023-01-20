from geoips.interfaces.base import BaseInterface, BasePlugin


class AlgorithmsInterface(BaseInterface):
    name = "algorithms"
    deprecated_family_attr = "alg_func_type"


algorithms = AlgorithmsInterface()


# class AlgorithmsPlugin(BasePlugin):
#     interface = algorithms
