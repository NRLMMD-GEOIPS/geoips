from geoips.interfaces.base import BaseInterface, BasePlugin


class InterpolatorsInterface(BaseInterface):
    """Interpolation routine to apply when reprojecting data."""
    name = "interpolators"
    entry_point_group = "interpolation"
    deprecated_family_attr = "interp_type"


interpolators = InterpolatorsInterface()

