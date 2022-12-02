from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class ProcflowsInterface(BaseInterface):
    name = 'procflows'
    deprecated_family_attr = 'procflow_type'


procflows = ProcflowsInterface()


class ProcflowsInterfacePlugin(BaseInterfacePlugin):
    interface = procflows
