"""Unit Test Module checking all functionality for text-based ascii_palette plugins."""

from matplotlib.colors import ListedColormap
import pytest

from geoips.interfaces import ascii_palettes


def generate_id(artifact):
    """Generate an test ID for the provided GeoIPS Artifact."""
    if hasattr(artifact, "id"):
        return str(artifact.id)
    elif hasattr(artifact, "name"):
        return str(artifact.name)


@pytest.mark.parametrize("plugin", ascii_palettes.get_plugins(), ids=generate_id)
def test_ascii_palette_plugin(plugin):
    """Perform unit tests on all ascii palette plugins

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
    for plugin in interface.get_plugins():
        assert plugin.id in interface.text_registry["ascii_palettes"]
    with pytest.raises(KeyError):
        interface.get_plugin("a_non_existent_plugin")
    assert interface.name == "ascii_palettes"
