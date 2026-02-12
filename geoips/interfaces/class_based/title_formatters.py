# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Title formatters interface class."""

from geoips.interfaces.base import BaseClassInterface


class TitleFormattersInterface(BaseClassInterface):
    """Interface for creating GeoIPS formatted titles."""

    name = "title_formatters"
    required_args = {"standard": []}
    required_kwargs = {"standard": []}


title_formatters = TitleFormattersInterface()
