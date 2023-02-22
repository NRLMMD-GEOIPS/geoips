from geoips.interfaces.base import BaseInterface, BasePlugin


class ReadersInterface(BaseInterface):
    """Interface for ingesting a specific data type.

    Provides specification for ingensting a specific data type, and storing in
    the GeoIPS xarray-based internal format.
    """
    name = "readers"
    deprecated_family_attr = "reader_type"
    required_args = {"standard": ["fnames"]}
    required_kwargs = {
        "standard": ["metadata_only", "chans", "area_def", "self_register"]
    }


readers = ReadersInterface()
