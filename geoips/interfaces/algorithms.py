from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class AlgorithmsInterface(BaseInterface):
    '''Interface for algorithm plugins.

    GeoIPS interface that provides access to algorithm plugins. This inherits all methods and attributes from
    BaseInterface.
    '''
    name = 'algorithms'
    deprecated_family_attr = 'alg_func_type'


algorithms = AlgorithmsInterface()


class AlgorithmsInterfacePlugin(BaseInterfacePlugin):
    interface = algorithms
