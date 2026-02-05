# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Title formatters interface class."""

from geoips.base_class_plugins import BaseTitleFormatterPlugin
from geoips.interfaces.base import BaseClassInterface


class TitleFormattersInterface(BaseClassInterface):
    """Interface for creating GeoIPS formatted titles."""

    name = "title_formatters"
    plugin_class = BaseTitleFormatterPlugin

    required_args = {"standard": []}
    required_kwargs = {"standard": []}


title_formatters = TitleFormattersInterface()
