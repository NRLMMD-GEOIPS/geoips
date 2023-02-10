from geoips.interfaces.base import BaseInterface, BasePlugin


class OutputFormatsInterface(BaseInterface):
    """Data format for the resulting output product (e.g. netCDF, png)."""
    name = "output_formats"
    deprecated_family_attr = "output_type"


output_formats = OutputFormatsInterface()

