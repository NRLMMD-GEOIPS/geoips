from geoips.interfaces.base import BaseInterface, BasePlugin


class TitleFormatsInterface(BaseInterface):
    """Interface for creating GeoIPS formatted titles."""
    name = "title_formats"
    entry_point_group = "title_formats"
    deprecated_family_attr = "title_type"
    required_args = {"standard": []}
    required_kwargs = {"standard": []}


title_formats = TitleFormatsInterface()
