from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class AlgorithmsInterface(BaseInterface):
    name = 'algorithms'
    deprecated_family_attr = 'alg_func_type'


algorithms = AlgorithmsInterface()


class AlgorithmsInterfacePlugin(BaseInterfacePlugin):
    interface = algorithms
