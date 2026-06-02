# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Title formatters interface class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseTitleFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS title_formatter plugins."""

    pass


class TitleFormattersInterface(BaseClassInterface):
    """Interface for creating GeoIPS formatted titles."""

    name = "title_formatters"
    plugin_class = BaseTitleFormatterPlugin

    required_args = {"standard": []}
    required_kwargs = {"standard": []}


title_formatters = TitleFormattersInterface()
