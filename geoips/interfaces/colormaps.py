from geoips.interfaces.base import BaseInterface, BasePlugin


class ColormapsInterface(BaseInterface):
    name = "colormaps"
    entry_point_group = "user_colormaps"
    deprecated_family_attr = "cmap_type"
    required_args = {
        "rgb": [],
        "ascii": [],
        "linear_segmented": [],
        "linear_norm": [],
        "product_based": [],
        "explicit": [],
        "builtin_matplotlib_cmap": ["data_range"],
    }

    required_kwargs = {
        "rgb": [],
        "ascii": [],
        "linear_segmented": ["data_range"],
        "linear_norm": ["data_range"],
        "product_based": ["product_name", "data_range"],
        "explicit": [],
        "builtin_matplotlib_cmap": ["cmap_name", "cbar_label", "create_colorbar"],
    }


colormaps = ColormapsInterface()
