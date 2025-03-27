# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""TestPluginRegistry Class used for Unit Testing the Plugin Registries."""

from glob import glob
from importlib import import_module, metadata
import logging
from os.path import basename, splitext
from pprint import pformat
import pytest
import json
import yaml

from geoips.plugin_registry import PluginRegistry
from geoips.errors import PluginRegistryError

LOG = logging.getLogger(__name__)


class PluginRegistryValidator(PluginRegistry):
    """Subclass of PluginRegistry which adds functionality for unit testing."""

    def __init__(self, fpaths=None):
        """Initialize TestPluginRegistry Class."""
        super().__init__("geoips.plugin_packages", _test_registry_files=fpaths)

    def validate_plugin_types_exist(self, reg_dict, reg_path):
        """Test that all top level plugin types exist in each registry file."""
        expected_plugin_types = ["yaml_based", "module_based", "text_based"]
        for p_type in expected_plugin_types:
            if p_type not in reg_dict:
                error_str = f"Expected plugin type '{p_type}' to be in the registry but"
                error_str += f" wasn't. This was in file '{reg_path}'."
                raise PluginRegistryError(error_str)

    def validate_all_registries(self):
        """Validate all registries in the current installation.

        This should be run during testing, but not at runtime.
        Ensure we do not fail catastrophically for a single bad plugin
        at runtime, so test up front to test validity.
        """
        for reg_path in self.registry_files:
            pkg_plugins = json.load(open(reg_path, "r"))
            self.validate_registry(pkg_plugins, reg_path)

    def validate_registry(self, current_registry, fpath):
        """Test all plugins found in registered plugins for their validity."""
        try:
            self.validate_plugin_types_exist(current_registry, fpath)
        except PluginRegistryError as e:
            # xfail if this is a test, otherwise just raise PluginRegistryError
            if self._is_test:
                pytest.xfail(str(e))
            else:
                raise PluginRegistryError(e)
        try:
            self.validate_registry_interfaces(current_registry)
        except PluginRegistryError as e:
            # xfail if this is a test, otherwise just raise PluginRegistryError
            if self._is_test:
                pytest.xfail(str(e))
            else:
                raise PluginRegistryError(e)
        for plugin_type in current_registry:
            for interface in current_registry[plugin_type]:
                for plugin in current_registry[plugin_type][interface]:
                    try:
                        if interface == "products":
                            for subplg in current_registry[plugin_type][interface][
                                plugin
                            ]:
                                self.validate_plugin_attrs(
                                    plugin_type,
                                    interface,
                                    (plugin, subplg),
                                    current_registry[plugin_type][interface][plugin][
                                        subplg
                                    ],
                                )
                        elif plugin_type != "text_based":
                            self.validate_plugin_attrs(
                                plugin_type,
                                interface,
                                plugin,
                                current_registry[plugin_type][interface][plugin],
                            )
                    except PluginRegistryError as e:
                        # xfail if this is a test,
                        # otherwise just raise PluginRegistryError
                        if self._is_test:
                            pytest.xfail(str(e))
                        else:
                            raise PluginRegistryError(e)

    def validate_plugin_attrs(self, plugin_type, interface, name, plugin):
        """Test non-product plugin for all required attributes."""
        missing = []
        if plugin_type == "yaml_based" and interface != "products":
            attrs = [
                "docstring",
                "family",
                "interface",
                "package",
                "plugin_type",
                "relpath",
            ]
        elif plugin_type == "yaml_based":
            attrs = [
                "docstring",
                "family",
                "interface",
                "package",
                "plugin_type",
                "product_defaults",
                "source_names",
                "relpath",
            ]
        else:
            attrs = [
                "docstring",
                "family",
                "interface",
                "package",
                "plugin_type",
                "signature",
                "relpath",
            ]
        for attr in attrs:
            try:
                plugin[attr]
            except KeyError:
                missing.append(attr)
        if missing:
            raise PluginRegistryError(
                f"Plugin '{name}' is missing the following required "
                f"top-level properties: '{missing}'"
            )

    def validate_registry_interfaces(self, current_registry):
        """Test Plugin Registry interfaces validity."""
        yaml_interfaces = []
        module_interfaces = []

        # NOTE: all <pkg>/interfaces/__init__.py files MUST
        # contain a "module_based_interfaces" list and a
        # "yaml_based_interfaces" list - this is how we
        # identify the valid interface names.
        # We must avoid actually importing the interfaces within
        # the geoips repo - or we will end up with a circular import
        # due to BaseInterface.
        for pkg in metadata.entry_points(group="geoips.plugin_packages"):
            try:
                mod = import_module(f"{pkg.value}.interfaces")
            except ModuleNotFoundError as resp:
                if f"No module named '{pkg.value}.interfaces'" in str(resp):
                    continue
                else:
                    raise ModuleNotFoundError(resp)
            module_interfaces += mod.module_based_interfaces
            yaml_interfaces += mod.yaml_based_interfaces

        bad_interfaces = []
        for plugin_type in ["module_based", "yaml_based"]:
            for interface in current_registry[plugin_type]:
                if (
                    interface not in module_interfaces
                    and interface not in yaml_interfaces
                ):
                    error_str = f"\nPlugin type '{plugin_type}' does not allow "
                    error_str += f"interface '{interface}'.\n"
                    error_str += "\nValid interfaces: "
                    if plugin_type == "module_based":
                        interface_list = module_interfaces
                    else:
                        interface_list = yaml_interfaces
                    error_str += f"\n{interface_list}\n"
                    error_str += "\nPlease update the following plugins "
                    error_str += "to use a valid interface:\n"
                    error_str += pformat(current_registry[plugin_type][interface])
                    bad_interfaces.append(error_str)
        if bad_interfaces:
            error_str = "The following interfaces were not valid:\n"
            for error in bad_interfaces:
                error_str += error
            raise PluginRegistryError(error_str)


class TestPluginRegistry:
    """
    Pytest-based Unit Test for the PluginRegistry Class.

    Note: Since we are not able to initlialize this class due to restrictions placed by
    Pytest, if you want to change the test files used, simply replace the location below
    with the location of your new test files.
    """

    default_fpaths = glob(
        str(__file__).replace("test_plugin_registries.py", "files/**/*.yaml"),
        recursive=True,
    )

    pr_validator = PluginRegistryValidator(default_fpaths)

    # Couldn't implement this class via inheritance because PyTest Raised this error:
    # PytestCollectionWarning: cannot collect test class 'TestPluginRegistry' because
    # it has a __init__ constructor (from: test_plugin_registries.py)

    # This isn't a problem though, as we can just set it as a class attribute and move
    # forward as usual. Pytest is just picky about having __init__ in Test Classes.

    # def __init__(self, fpaths=default_fpaths):
    #     super().__init__(fpaths)

    def generate_id(fpath):
        """Generate pytest id for current test."""
        test_id = "bad"
        if "/good/" in fpath:
            test_id = "good"
        return f"{test_id}-{splitext(basename(fpath))[0]}"

    def test_registered_plugin_property(self):
        """Ensure registered_plugins is valid in its nature."""
        print(self.pr_validator.registered_plugins)
        assert isinstance(self.pr_validator.registered_plugins, dict)
        assert "yaml_based" in self.pr_validator.registered_plugins
        assert "module_based" in self.pr_validator.registered_plugins
        assert "text_based" in self.pr_validator.registered_plugins

    def test_interface_mapping_property(self):
        """Ensure interface_mapping is valid in its nature."""
        print(self.pr_validator.interface_mapping)
        assert isinstance(self.pr_validator.interface_mapping, dict)
        assert "yaml_based" in self.pr_validator.interface_mapping
        assert "module_based" in self.pr_validator.interface_mapping
        assert "text_based" in self.pr_validator.interface_mapping
        assert isinstance(self.pr_validator.interface_mapping["yaml_based"], list)
        assert isinstance(self.pr_validator.interface_mapping["module_based"], list)
        assert isinstance(self.pr_validator.interface_mapping["text_based"], list)

    @pytest.mark.parametrize("fpath", pr_validator.registry_files, ids=generate_id)
    def test_all_registries(self, fpath):
        """Test all available yaml registries."""
        current_registry = yaml.safe_load(open(fpath, "r"))
        self.pr_validator.validate_registry(current_registry, fpath)
