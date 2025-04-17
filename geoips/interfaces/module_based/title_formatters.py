# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Title formatters interface module."""

from geoips.interfaces.base import BaseModuleInterface


class TitleFormattersInterface(BaseModuleInterface):
    """Interface for creating GeoIPS formatted titles."""

    name = "title_formatters"
    required_args = {"standard": []}
    required_kwargs = {"standard": []}


title_formatters = TitleFormattersInterface()
