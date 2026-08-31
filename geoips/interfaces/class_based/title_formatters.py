# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Title formatters interface class."""

from geoips.interfaces.base import BaseClassInterface


class TitleFormattersInterface(BaseClassInterface):
    """Interface for creating GeoIPS formatted titles."""

    from geoips.interfaces.class_based.bases import BaseTitleFormatterPlugin

    name = "title_formatters"
    plugin_class = BaseTitleFormatterPlugin

    required_args = {"standard": []}
    required_kwargs = {"standard": []}


title_formatters = TitleFormattersInterface()
