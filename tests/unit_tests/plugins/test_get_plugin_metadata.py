# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test for the interface method 'get_plugin_metadata'."""

import pytest

from geoips import interfaces
from geoips.errors import PluginRegistryError


def generate_id(iname_pname):
    """Generate an ID for the test-arguments provided."""
    interface = iname_pname[0]
    plugin_name = iname_pname[1]
    if isinstance(plugin_name, tuple):
        return f"{interface} " + " ".join(plugin_name)
    return f"{interface} {str(plugin_name)}"


int_plg_pairs = []

idict = interfaces.list_available_interfaces()

for itype in idict:
    for iname in idict[itype]:
        interface = getattr(interfaces, iname)
        iregistry = interface.plugin_registry.registered_plugins.get(itype, {}).get(
            iname
        )
        if iregistry:
            if iname != "products":
                for pname in iregistry:
                    int_plg_pairs.append([iname, pname])
            else:
                for sname in iregistry:
                    for pname in iregistry[sname]:
                        int_plg_pairs.append([iname, (sname, pname)])

int_plg_pairs.append(["fake_interface", "fake_plugin"])
int_plg_pairs.append(["algorithms", 2])
int_plg_pairs.append(["algorithms", "non_existent_plugin"])


@pytest.mark.parametrize(
    "iname_pname",
    int_plg_pairs,
    ids=generate_id,
)
def test_get_plugin_metadata(iname_pname):
    """Test that <interface_name>.get_plugin_metadata(<name>) works as expected.

    Includes failing cases as well. This should hit 100% coverage for the new code.
    """
    iname = iname_pname[0]
    pname = iname_pname[1]

    if iname == "fake_interface":
        interface = getattr(interfaces, "algorithms")
        interface.interface_type = "some_fake_type"
        # Failing case 1
        with pytest.raises(KeyError):
            md = interface.get_plugin_metadata(pname)
        # Make sure to reset the interface type; algorithms will need this later on
        interface.interface_type = "module_based"
        return
    else:
        interface = getattr(interfaces, iname)

    if isinstance(pname, tuple):
        md = interface.get_plugin_metadata(*pname)
    else:
        # Failing case 2
        if pname == 2:
            with pytest.raises(TypeError):
                md = interface.get_plugin_metadata(pname)
            return
        # Failing case 3
        elif pname == "non_existent_plugin":
            with pytest.raises(PluginRegistryError):
                md = interface.get_plugin_metadata(pname)
            return
        # Any other case should pass
        else:
            md = interface.get_plugin_metadata(pname)

    # All of these keys should exist for every plugin type
    for key in [
        "docstring",
        "family",
        "interface",
        "package",
        "plugin_type",
        "relpath",
    ]:
        assert key in md
