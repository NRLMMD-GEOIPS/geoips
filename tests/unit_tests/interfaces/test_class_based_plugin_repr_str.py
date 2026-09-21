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

    def test_repr_without_module_reports_unknown_package(self):
        """Verify a plugin created without a module reports package 'Unknown'."""
        plugin = _FakeReprPlugin()
        assert repr(plugin) == (
            "_FakeReprPlugin(name='fake_repr', interface='algorithms', "
            "package='Unknown')"
        )

    def test_repr_derives_package_from_module_name(self):
        """Verify the package is the first dot-separated part of the module name."""
        plugin = _FakeReprPlugin(_make_fake_module("some_pkg.plugins.fake_module"))
        assert repr(plugin) == (
            "_FakeReprPlugin(name='fake_repr', interface='algorithms', "
            "package='some_pkg')"
        )

    def test_repr_module_name_without_dot_is_used_whole(self):
        """Verify a module name with no dot is used as the package as-is."""
        plugin = _FakeReprPlugin(_make_fake_module("toplevel"))
        assert repr(plugin) == (
            "_FakeReprPlugin(name='fake_repr', interface='algorithms', "
            "package='toplevel')"
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

    def test_str_without_module_reports_unknown_package(self):
        """Verify a plugin created without a module reads as coming from Unknown."""
        plugin = _FakeReprPlugin()
        assert str(plugin) == "fake_repr (algorithms plugin from Unknown)"

    def test_str_derives_package_from_module_name(self):
        """Verify `__str__` uses the package derived from the module name."""
        plugin = _FakeReprPlugin(_make_fake_module("some_pkg.plugins.fake_module"))
        assert str(plugin) == "fake_repr (algorithms plugin from some_pkg)"


class TestClassBasedPluginInvalidName:
    """Tests for plugins whose `name` is missing or unusable."""

    @pytest.mark.parametrize("bad_name", ["", None, 123])
    def test_invalid_name_is_omitted_and_str_falls_back_to_repr(self, bad_name):
        """Verify an unusable name is omitted and `__str__` falls back to `__repr__`.

        `__init_subclass__` rejects plugin classes without a valid name, so the class
        attribute is shadowed on the instance instead.
        """
        plugin = _FakeReprPlugin()
        plugin.name = bad_name
        expected_repr = "_FakeReprPlugin(interface='algorithms', package='Unknown')"
        assert repr(plugin) == expected_repr
        assert str(plugin) == expected_repr


class TestClassBasedPluginFromRegistry:
    """Tests using a real plugin loaded through the plugin registry."""

    def test_real_reader_repr_and_str(self):
        """Verify a registered reader reports its real class, interface, and package."""
        plugin = readers.get_plugin("abi_netcdf")
        assert repr(plugin) == (
            "AbiNetcdfReaderPlugin(name='abi_netcdf', interface='readers', "
            "package='geoips')"
        )
        assert str(plugin) == "abi_netcdf (readers plugin from geoips)"
