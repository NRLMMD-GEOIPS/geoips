from geoips.interfaces.base_interface import BaseInterface

class AlgorithmsInterface(BaseInterface):
    name = 'algorithms'
    deprecated_family_attr = 'alg_func_type'

algorithms = AlgorithmsInterface()