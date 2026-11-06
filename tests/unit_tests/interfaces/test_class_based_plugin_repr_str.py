# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for the `__repr__` and `__str__` methods of `BaseClassPlugin`."""

import types

import pytest

from geoips.interfaces import readers
from geoips.interfaces.class_based_plugin import BaseClassPlugin


class _FakeReprPlugin(BaseClassPlugin):
    """Minimal class-based plugin used to exercise `__repr__` and `__str__`."""

    interface = "algorithms"
    family = "test"
    name = "fake_repr"

    def call(self, data=None, **kwargs):
        return data


def _make_fake_module(module_name):
    """Build a stand-in module object that `BaseClassPlugin.__init__` accepts.

    `types.ModuleType` does not set `__file__`, but `BaseClassPlugin.__init__` reads
    it, so it is assigned here.
    """
    fake_module = types.ModuleType(module_name)
    fake_module.__file__ = f"/fake/path/{module_name.replace('.', '/')}.py"
    return fake_module


class TestClassBasedPluginRepr:
    """Tests for `BaseClassPlugin.__repr__`."""

    def test_repr_without_module_reports_unnamed_module_package(self):
        """Verify a plugin created without a module reports 'UnnamedModule'."""
        plugin = _FakeReprPlugin()
        assert repr(plugin) == (
            "_FakeReprPlugin(interface='algorithms', module_name='UnnamedModule', "
            "name='fake_repr', package='UnnamedModule')"
        )

    def test_repr_derives_package_from_module_name(self):
        """Verify the package is the first dot-separated part of the module name."""
        plugin = _FakeReprPlugin(_make_fake_module("some_pkg.plugins.fake_module"))
        assert repr(plugin) == (
            "_FakeReprPlugin(interface='algorithms', "
            "module_name='some_pkg.plugins.fake_module', name='fake_repr', "
            "package='some_pkg')"
        )

    def test_repr_module_name_without_dot_is_used_whole(self):
        """Verify a module name with no dot is used as the package as-is."""
        plugin = _FakeReprPlugin(_make_fake_module("toplevel"))
        assert repr(plugin) == (
            "_FakeReprPlugin(interface='algorithms', module_name='toplevel', "
            "name='fake_repr', package='toplevel')"
        )

    def test_repr_of_list_is_one_line_per_plugin(self):
        """Verify a list of plugins reprs without any embedded newlines."""
        first_plugin = _FakeReprPlugin()
        second_plugin = _FakeReprPlugin(_make_fake_module("some_pkg.fake_module"))
        list_repr = repr([first_plugin, second_plugin])
        assert "\n" not in list_repr
        assert repr(first_plugin) in list_repr
        assert repr(second_plugin) in list_repr


class TestClassBasedPluginStr:
    """Tests for `BaseClassPlugin.__str__`."""

    def test_str_without_module_reports_unnamed_module_package(self):
        """Verify a plugin created without a module reads as from UnnamedModule."""
        plugin = _FakeReprPlugin()
        assert str(plugin) == "fake_repr (algorithms plugin from UnnamedModule)"

    def test_str_derives_package_from_module_name(self):
        """Verify `__str__` uses the package derived from the module name."""
        plugin = _FakeReprPlugin(_make_fake_module("some_pkg.plugins.fake_module"))
        assert str(plugin) == "fake_repr (algorithms plugin from some_pkg)"

    def test_str_without_interface_reports_no_interface(self):
        """Verify a plugin with no interface reads as a 'NoInterface plugin'."""
        plugin = _FakeReprPlugin()
        plugin.interface = None
        assert str(plugin) == "fake_repr (NoInterface plugin from UnnamedModule)"


class TestClassBasedPluginInvalidName:
    """Tests for plugins whose `name` is empty or not a string.

    `__init_subclass__` rejects plugin classes without a valid name, so the class
    attribute is shadowed on the instance instead.
    """

    @pytest.mark.parametrize(
        "falsy_name, expected_repr",
        [
            (
                "",
                "_FakeReprPlugin(interface='algorithms', "
                "module_name='UnnamedModule', name='', package='UnnamedModule')",
            ),
            (
                None,
                "_FakeReprPlugin(interface='algorithms', "
                "module_name='UnnamedModule', name=None, package='UnnamedModule')",
            ),
        ],
    )
    def test_falsy_name_is_shown_and_str_falls_back_to_repr(
        self, falsy_name, expected_repr
    ):
        """Verify a falsy name still appears in `__repr__`, which `__str__` returns."""
        plugin = _FakeReprPlugin()
        plugin.name = falsy_name
        assert repr(plugin) == expected_repr
        assert str(plugin) == expected_repr

    def test_non_string_name_is_shown_in_repr_and_str(self):
        """Verify a truthy non-string name is printed as-is by both methods."""
        plugin = _FakeReprPlugin()
        plugin.name = 123
        assert repr(plugin) == (
            "_FakeReprPlugin(interface='algorithms', module_name='UnnamedModule', "
            "name=123, package='UnnamedModule')"
        )
        assert str(plugin) == "123 (algorithms plugin from UnnamedModule)"


class TestClassBasedPluginFromRegistry:
    """Tests using a real plugin loaded through the plugin registry."""

    def test_real_reader_repr_and_str(self):
        """Verify a registered reader reports its real class, interface, and package."""
        plugin = readers.get_plugin("abi_netcdf")
        assert repr(plugin) == (
            "AbiNetcdfReaderPlugin(interface='readers', "
            "module_name='geoips.plugins.classes.readers.abi_netcdf', "
            "name='abi_netcdf', package='geoips')"
        )
        assert str(plugin) == "abi_netcdf (readers plugin from geoips)"
