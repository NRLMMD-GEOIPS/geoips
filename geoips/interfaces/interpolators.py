from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class InterpolatorsInterface(BaseInterface):
    name = "interpolators"
    entry_point_group = "interpolation"
    deprecated_family_attr = "interp_type"


interpolators = InterpolatorsInterface()


class InterpolatorsInterfacePlugin(BaseInterfacePlugin):
    interface = interpolators
