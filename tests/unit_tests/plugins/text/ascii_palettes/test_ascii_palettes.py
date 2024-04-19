"""Unit Test Module checking all functionality for text-based ascii_palette plugins."""

from glob import glob
from matplotlib.colors import ListedColormap
from os.path import basename
import pytest

from geoips.errors import AsciiPaletteError, PluginError

# Using from_ascii rather than geoips.interfaces.ascii_palettes.AsciiPaletteColormap
# because that requires the corresponding ascii_palette to be in the plugin registry,
# which we don't want. They do the exact same thing currently.
from geoips.image_utils.colormap_utils import from_ascii
from geoips.interfaces import ascii_palettes
from geoips.interfaces.text_based import get_required_attrs


def generate_id(artifact):
    """Generate an test ID for the provided GeoIPS Artifact."""
    if hasattr(artifact, "id"):
        # This is an ascii plugin
        return str(artifact.id)
    elif hasattr(artifact, "name"):
        # This is the ascii palette interface
        return str(artifact.name)
    else:
        # This is the path to an ascii_palette text file
        return str(basename(artifact))


@pytest.mark.parametrize("plugin", ascii_palettes.get_plugins(), ids=generate_id)
def test_ascii_palette_plugin(plugin):
    """Perform unit tests on all ascii palette plugins.

    Parameters
    ----------
    plugin: AsciiPalettePlugin
        - A GeoIPS AsciiPalettePlugin generated from an ascii palette .txt file
    """
    # check that the ascii palette plugin has an identifier
    assert plugin.id
    # assert this plugin is in the registry
    assert plugin.id in ascii_palettes.text_registry["ascii_palettes"]
    # assert that this plugin's interface is the ascii palette interface
    assert plugin.interface == "ascii_palettes"
    # check that there has been a Matplotlib.colors.ListedColormap created the plugin
    assert isinstance(plugin.colormap, ListedColormap)


@pytest.mark.parametrize("interface", [ascii_palettes], ids=generate_id)
def test_ascii_palette_interface(interface):
    """Perform unit tests on the ascii palette interface.

    Parameters
    ----------
    interface: AsciiPaletteInterface
        - The ascii palette text-based interface that we want to test.
    """
    assert "BaseTextInterface" in str(interface.__class__.__base__)
    # make sure that every plugin is in the ascii_palettes portion of the plugin
    # registry
    for plugin in interface.get_plugins():
        assert plugin.id in interface.text_registry["ascii_palettes"]
    with pytest.raises(KeyError):
        # assert that retrieving a plugin that doesn't exist causes an error
        interface.get_plugin("a_non_existent_plugin")
    # make sure the interface is named ascii_palettes
    assert interface.name == "ascii_palettes"


@pytest.mark.parametrize(
    "palette_path",
    glob(str(__file__).replace("test_ascii_palettes.py", "example_palettes/*.txt")),
    ids=generate_id,
)
def test_ascii_palette_file(palette_path):
    """Unit Tests for ensuring we catch all errors related to an ascii palette file.

    Parameters
    ----------
    palette_path: str
        - The full path to the ascii palette file we want to test.
    """
    if basename(palette_path) in ["missing_docstring.txt", "missing_required_attr.txt"]:
        # ascii_palette plugin source file is missing a required attribute
        # make sure a PluginError is raised for those files
        with pytest.raises(PluginError):
            get_required_attrs(palette_path)
    else:
        # Otherwise the file had all of the required attributes
        attrs = get_required_attrs(palette_path)
        # Ensure that every required attribute was found in the returned dictionary
        for key in ["interface", "name", "family", "doc", "plugin_type"]:
            assert key in attrs.keys()

        if basename(palette_path) in ["invalid_palette.txt", "missing_palette.txt"]:
            # These are invalid ascii palettes. Make sure an AsciiPaletteError is raised
            # when trying to convert them to a colormap
            with pytest.raises(AsciiPaletteError):
                from_ascii(palette_path)
        elif basename(palette_path) == "good.txt":
            # this ascii palette file is good. Make sure the colormap retrieved from it
            # is a ListedColormap Object
            cmap = from_ascii(palette_path)
            assert isinstance(cmap, ListedColormap)
