# # # This source code is subject to the license referenced at
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

from geoips.errors import PluginError, PluginRegistryError
from geoips.filenames.base_paths import PATHS
from geoips.interfaces import algorithms, products, sectors, workflows
from geoips.plugin_registry import PluginRegistry

LOG = logging.getLogger(__name__)


class FakeInterface:
    """Dummy fake interface used to cause appropriate errors from the PluginRegistry."""

    interface_type = "fake"
    name = "fake_interface"


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

    Note: Since we are not able to initialize this class due to restrictions placed by
    Pytest, if you want to change the test files used, simply replace the location below
    with the location of your new test files.
    """

    default_fpaths = glob(
        str(__file__).replace("test_plugin_registries.py", "files/**/*.yaml"),
        recursive=True,
    )

    # pr_validator uses test registry files for most tests
    pr_validator = PluginRegistryValidator(fpaths=default_fpaths)
    # real reg validator is responsible for testing deleting and building of registries
    # based on whether or not we want that to occur:
    # I.e. whether or not PATHS["GEOIPS_REBUILD_REGISTRIES"] is set to True or False
    real_reg_validator = PluginRegistryValidator(fpaths=None)

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
        if hasattr(self.pr_validator, "_registered_plugins"):
            del self.pr_validator._registered_plugins
        print(self.pr_validator.registered_plugins)
        assert isinstance(self.pr_validator.registered_plugins, dict)
        assert "yaml_based" in self.pr_validator.registered_plugins
        assert "module_based" in self.pr_validator.registered_plugins
        assert "text_based" in self.pr_validator.registered_plugins
        assert self.pr_validator.registered_plugins

    def test_interface_mapping_property(self):
        """Ensure interface_mapping is valid in its nature."""
        if hasattr(self.pr_validator, "_interface_mapping"):
            del self.pr_validator._interface_mapping
        if hasattr(self.pr_validator, "_registered_plugins"):
            del self.pr_validator._registered_plugins
        print(self.pr_validator.interface_mapping)
        assert isinstance(self.pr_validator.interface_mapping, dict)
        assert "yaml_based" in self.pr_validator.interface_mapping
        assert "module_based" in self.pr_validator.interface_mapping
        assert "text_based" in self.pr_validator.interface_mapping
        assert isinstance(self.pr_validator.interface_mapping["yaml_based"], list)
        assert isinstance(self.pr_validator.interface_mapping["module_based"], list)
        assert isinstance(self.pr_validator.interface_mapping["text_based"], list)

    def test_registered_module_plugins_property(self):
        """Ensure that registered_module_plugins exist and have contents."""
        if hasattr(self.pr_validator, "_registered_plugins"):
            del self.pr_validator._registered_plugins
        print(self.pr_validator.registered_module_based_plugins)
        assert isinstance(self.pr_validator.registered_module_based_plugins, dict)
        assert len(self.pr_validator.registered_module_based_plugins)

    def test_registered_yaml_plugins_property(self):
        """Ensure that registered_yaml_plugins exist and have contents."""
        if hasattr(self.pr_validator, "_registered_plugins"):
            del self.pr_validator._registered_plugins
        print(self.pr_validator.registered_yaml_based_plugins)
        assert isinstance(self.pr_validator.registered_yaml_based_plugins, dict)
        assert len(self.pr_validator.registered_yaml_based_plugins)

    def test_automatic_registry_creation(self):
        """Assert that the registries are automatically rebuilt.

        This occurs if expected registry files are missing and
        PATHS["GEOIPS_REBUILD_REGISTRIES"] is set to True.
        """
        PATHS["GEOIPS_REBUILD_REGISTRIES"] = True
        self.real_reg_validator.delete_registries()
        # Delete again using specific packages (won't do anything) for code coverage
        self.real_reg_validator.delete_registries(packages=["geoips"])
        self.real_reg_validator._set_class_properties(force_reset=True)
        assert self.real_reg_validator.registered_plugins

    def test_disabled_registry_creation(self):
        """Assert that the registries are not automatically rebuilt.

        This occurs if expected registry files are missing and
        PATHS["GEOIPS_REBUILD_REGISTRIES"] is set to False. A FileNotFoundError should
        be raised.
        """
        PATHS["GEOIPS_REBUILD_REGISTRIES"] = False
        self.real_reg_validator.delete_registries()
        with pytest.raises(FileNotFoundError):
            self.real_reg_validator._set_class_properties(force_reset=True)

    def test_get_plugin_metadata(self):
        """Retrieve plugin metadata from a plugin that we know exists and is correct.

        For this test, we'll be using the algorithms.single_channel plugin and the
        products.abi.Infrared plugin.
        """
        PATHS["GEOIPS_REBUILD_REGISTRIES"] = True
        self.real_reg_validator._set_class_properties(force_reset=True)
        assert algorithms.get_plugin_metadata("single_channel")
        assert products.get_plugin_metadata("abi", "Infrared")

    def test_get_plugin_metadata_failing_cases(self):
        """Attempt to retrieve plugin metadata from a cases that we know should fail."""
        PATHS["GEOIPS_REBUILD_REGISTRIES"] = True
        self.real_reg_validator._set_class_properties(force_reset=True)
        # Caused when a plugin doesn't exist under an interface's registry
        with pytest.raises(PluginRegistryError):
            algorithms.get_plugin_metadata("fake_plugin")
        # Caused due to invalid argument type
        with pytest.raises(TypeError):
            algorithms.get_plugin_metadata(1078)

        # Caused due to the registry being unable to locate this interface of a certain
        # type
        with pytest.raises(KeyError):
            self.real_reg_validator.get_plugin_metadata(FakeInterface, "fake_plugin")

    def test_get_yaml_plugin(self):
        """Retrieve valid (existing and formatted correctly) GeoIPS YAML plugin(s).

        Will retrieve ('abi', 'Infrared') product, 'goes_east' sector, and
        'abi_infrared' workflow plugins, as those all hit different portions of the
        codebase.
        """
        prd = self.real_reg_validator.get_yaml_plugin(products, ("abi", "Infrared"))
        sect = self.real_reg_validator.get_yaml_plugin(sectors, "goes_east")
        wrkflw = self.real_reg_validator.get_yaml_plugin(workflows, "abi_infrared")

        if isinstance(prd, dict):
            assert prd["name"] == "Infrared"
            assert prd["interface"] == "products"
            assert "abi" in prd["source_names"]

            assert sect["name"] == "goes_east"
            assert sect["interface"] == "sectors"

        else:
            assert wrkflw.name == "abi_infrared"
            assert wrkflw.interface == "workflows"

    def test_get_yaml_plugin_failing_cases(self):
        """Attempt to get all plugins from an interface using cases that should fail."""
        # Reconstruct the registry in memory so we start at a clean slate
        self.real_reg_validator._set_class_properties(force_reset=True)
        # Set interfaces' rebuild_registries attr to false for the time being
        sectors.rebuild_registries = False
        products.rebuild_registries = False
        workflows.rebuild_registries = False

        yam_reg = self.real_reg_validator.registered_plugins.pop("yaml_based")
        # Caused due to 'yaml_based' plugins being absent from the registry
        with pytest.raises(PluginError):
            self.real_reg_validator.get_yaml_plugin(sectors, "goes_east")
        # Reset the yaml_based portion of the registry back to its original value
        self.real_reg_validator.registered_plugins["yaml_based"] = yam_reg

        # Caused due to invalid argument type (rebuild_registries) should be a boolean
        with pytest.raises(TypeError):
            self.real_reg_validator.get_yaml_plugin(
                sectors, "goes_east", rebuild_registries=Exception
            )

        # Caused due to a missing plugin
        with pytest.raises(PluginError):
            self.real_reg_validator.get_yaml_plugin(
                products, ("abi", "fake_plugin"), rebuild_registries=False
            )

        abi_infrared_relpath = self.real_reg_validator.registered_yaml_based_plugins[
            "products"
        ]["abi"]["Infrared"].pop("relpath")
        self.real_reg_validator.registered_yaml_based_plugins["products"]["abi"][
            "Infrared"
        ]["relpath"] = "/some/fake/path.yaml"
        # Caused due to non existent file path
        with pytest.raises(PluginRegistryError):
            self.real_reg_validator.get_yaml_plugin(products, ("abi", "Infrared"))
        # Reset that relative path back to its original value
        self.real_reg_validator.registered_yaml_based_plugins["products"]["abi"][
            "Infrared"
        ]["relpath"] = abi_infrared_relpath

        fake_plugin_entry = {
            "docstring": "The 89VNearest product_defaults for gmi product.",
            "family": None,
            "interface": "products",
            "package": "geoips",
            "plugin_type": "yaml_based",
            "product_defaults": "89VNearest",
            "source_names": ["gmi"],
            "relpath": "plugins/yaml/products/gmi.yaml",
        }
        self.real_reg_validator.registered_plugins["yaml_based"]["products"]["gmi"][
            "fake_plugin"
        ] = fake_plugin_entry
        # Caused due to products plugin being found in the registry but doesn't exist
        # in the actual file specified
        with pytest.raises(PluginError):
            self.real_reg_validator.get_yaml_plugin(products, ("gmi", "fake_plugin"))
        # Remove the fake entry from the registry
        self.real_reg_validator.registered_plugins["yaml_based"]["products"]["gmi"].pop(
            "fake_plugin"
        )

        # Caused due to a missing plugin (that's not a products plugin)
        with pytest.raises(PluginError):
            self.real_reg_validator.get_yaml_plugin(sectors, "fake_plugin")

        goes_east_relpath = self.real_reg_validator.registered_yaml_based_plugins[
            "sectors"
        ]["goes_east"].pop("relpath")
        self.real_reg_validator.registered_yaml_based_plugins["sectors"]["goes_east"][
            "relpath"
        ] = "/some/fake/path.yaml"
        # Caused due to non existent file path
        with pytest.raises(PluginRegistryError):
            self.real_reg_validator.get_yaml_plugin(sectors, "goes_east")
        # Reset that relative path back to its original value
        self.real_reg_validator.registered_yaml_based_plugins["sectors"]["goes_east"][
            "relpath"
        ] = goes_east_relpath

        fake_plugin_entry = {
            "docstring": "ABI DWM High Workflow.",
            "family": "order_based",
            "interface": "workflows",
            "package": "geoips",
            "plugin_type": "yaml_based",
            "relpath": "plugins/yaml/workflows/abi.yaml",
        }
        self.real_reg_validator.registered_plugins["yaml_based"]["workflows"][
            "fake_plugin"
        ] = fake_plugin_entry
        # Caused due to workflow plugin being present in registry but not in
        # corresponding plugin
        with pytest.raises(PluginError):
            self.real_reg_validator.get_yaml_plugin(workflows, "fake_plugin")
        # Remove the fake entry from the registry
        self.real_reg_validator.registered_plugins["yaml_based"]["workflows"].pop(
            "fake_plugin"
        )
        # This test misses line #426 as that is a pydantic check. Can't test this
        # until we switch over to that.
        # Reset interfaces' rebuild_registries values to True
        products.rebuild_registries = True
        sectors.rebuild_registries = True
        workflows.rebuild_registries = True

    def test_get_yaml_plugins(self):
        """Retrieve valid (existing and formatted correctly) GeoIPS YAML plugins.

        This tests PluginRegistry.get_yaml_plugins, in this case, using the sectors
        interface.
        """
        self.real_reg_validator._set_class_properties(force_reset=True)
        assert len(self.real_reg_validator.get_yaml_plugins(sectors))

    def test_get_yaml_plugins_failing_cases(self):
        """Attempt to retrieve all yaml plugins from a fake interface."""
        plugins = self.real_reg_validator.get_yaml_plugins(FakeInterface)
        assert len(plugins) == 0

    def test_get_module_plugin(self):
        """Retrieve a valid (existing and formatted correctly) module plugin.

        In this test case, we are using algorithms.single_channel.
        """
        self.real_reg_validator._set_class_properties(force_reset=True)
        alg = self.real_reg_validator.get_module_plugin(algorithms, "single_channel")
        assert alg.name == "single_channel"
        assert alg.interface == "algorithms"

    def test_get_module_plugin_failing_cases(self):
        """Attempt to retrieve a module plugin using cases that we know will fail."""
        # Reconstruct the registry in memory so we start at a clean slate
        self.real_reg_validator._set_class_properties(force_reset=True)
        # Set algorithms' rebuild_registry attr to false for the time being
        algorithms.rebuild_registries = False
        mod_reg = self.real_reg_validator.registered_plugins.pop("module_based")
        # Caused due to 'module_based' not being at the top level of the registry
        with pytest.raises(PluginError):
            self.real_reg_validator.get_module_plugin(algorithms, "single_channel")
        # Reset the registry to its original state
        self.real_reg_validator.registered_plugins["module_based"] = mod_reg

        # Caused due to invalid argument type (rebuild_registries) should be a boolean
        with pytest.raises(TypeError):
            self.real_reg_validator.get_module_plugin(
                algorithms, "single_channel", rebuild_registries=Exception
            )

        # Caused due to a missing plugin
        with pytest.raises(PluginError):
            self.real_reg_validator.get_module_plugin(
                algorithms, "fake_plugin", rebuild_registries=False
            )

        fake_plugin_entry = {
            "docstring": (
                "Data manipulation steps for standard 'single_channel' algorithm.\n"
                "Generalized algorithm to apply data manipulation steps in a standard "
                "order to apply corrections to a single channel output product."
            ),
            "family": "list_numpy_to_numpy",
            "interface": "algorithms",
            "package": "geoips",
            "plugin_type": "module_based",
            "signature": (
                "(arrays, output_data_range=None, input_units=None, output_units=None, "
                "min_outbounds='crop', max_outbounds='crop', norm=False, inverse=False,"
                " sun_zen_correction=False, mask_night=False, max_day_zen=None, "
                "mask_day=False, min_night_zen=None, gamma_list=None, "
                "scale_factor=None, satellite_zenith_angle_cutoff=None)"
            ),
            "relpath": "/some/fake/path.py",
        }
        self.real_reg_validator.registered_plugins["module_based"]["algorithms"][
            "fake_plugin"
        ] = fake_plugin_entry
        # Caused due to algorithm plugin being present in registry it's relative path
        # does not exist
        with pytest.raises(PluginRegistryError):
            self.real_reg_validator.get_module_plugin(algorithms, "fake_plugin")
        # Remove the fake entry from the registry
        self.real_reg_validator.registered_plugins["module_based"]["algorithms"].pop(
            "fake_plugin"
        )
        # reset algorithms' rebuild_registries attr to true
        algorithms.rebuild_registries = True

    def test_get_module_plugins(self):
        """Retrieve valid (existing and formatted correctly) module plugins.

        In this case, we are retrieving all GeoIPS module algorithm plugins.
        """
        self.real_reg_validator._set_class_properties(force_reset=True)
        assert len(self.real_reg_validator.get_module_plugins(algorithms))

    def test_get_module_plugins_failing_cases(self):
        """Attempt to retrieve all module plugins from a fake interface."""
        plugins = self.real_reg_validator.get_module_plugins(FakeInterface)
        assert len(plugins) == 0

    def test_retry_get_plugin(self):
        """Test that PluginRegistry.retry_get_plugin works as expected."""
        with pytest.raises(PluginError):
            self.real_reg_validator.get_module_plugin(
                algorithms, "fake_plugin", rebuild_registries=True
            )

    def test_create_registries_invalid_input(self):
        """Assert ValueError is raised when invalid input is sent to create_registries.

        Where 'create_registries' comes from PluginRegistry.
        """
        # Caused due to invalid input. save_type must be one of ['json', 'yaml']
        with pytest.raises(ValueError):
            self.real_reg_validator.create_registries(save_type="log")

    def test_create_registries_with_specific_packages(self, caplog):
        """Test that create_registries works with a subset of packages provided.

        In this case, packages = ['geoips'].
        """
        # 10 is the level of LOG.debug
        with caplog.at_level(logging.DEBUG):
            self.real_reg_validator.create_registries(packages=["geoips"])

        debug_logs = [
            record.message
            for record in caplog.records
            if record.levelno == logging.DEBUG
        ]
        assert any(["geoips" in message for message in debug_logs])

    def test_delete_registries_with_invalid_input(self):
        """Call delete_registries with invalid input and assert that errors are raised.

        Where the expected errors are TypeErrors or PluginRegistryErrors.
        """
        # Not a list
        with pytest.raises(TypeError):
            self.real_reg_validator.delete_registries(packages=Exception)
        # Not a list of strings
        with pytest.raises(TypeError):
            self.real_reg_validator.delete_registries(packages=[1, 2, 3, 4])
        # Not a valid package under namespace 'geoips.plugin_packages'
        with pytest.raises(PluginRegistryError):
            self.real_reg_validator.delete_registries(packages=["some_fake_package"])

    @pytest.mark.parametrize("fpath", pr_validator.registry_files, ids=generate_id)
    def test_all_registries(self, fpath):
        """Test all available yaml registries."""
        with open(fpath, "r") as fo:
            current_registry = yaml.safe_load(fo)
        self.pr_validator.validate_registry(current_registry, fpath)
