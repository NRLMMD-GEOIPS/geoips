from geoips.interfaces.base_interface import BaseInterface

class ProcflowsInterface(BaseInterface):
    name = 'procflows'
    deprecated_family_attr = 'procflow_type'

procflows = ProcflowsInterface()
