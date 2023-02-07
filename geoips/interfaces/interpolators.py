from geoips.interfaces.base import BaseInterface, BasePlugin


class InterpolatorsInterface(BaseInterface):
    name = "interpolators"
    entry_point_group = "interpolation"
    deprecated_family_attr = "interp_type"


interpolators = InterpolatorsInterface()

