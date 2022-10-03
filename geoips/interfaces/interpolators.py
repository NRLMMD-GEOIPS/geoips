from geoips.interfaces.base_interface import BaseInterface

class InterpolatorsInterface(BaseInterface):
    name = 'interpolators'
    entry_point = 'interpolation'
    deprecated_family_attr = 'interp_type'

interpolators = InterpolatorsInterface()