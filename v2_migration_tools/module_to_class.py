"""Script which converts all module based plugins from a package to class based."""

# cspell:ignore geoips, fpaths

import inspect
from importlib import resources, util
import os

from geoips.utils.types.partial_lexeme import Lexeme
from geoips import interfaces
from geoips.interfaces import class_based

from cst_transformer import convert_single_file


def get_class_name(interface_name, plugin_name):
    """Generate a class' name from its interface type and its plugin name."""
    plugin_interface_name = Lexeme(interface_name).singular.title().replace("_", "")
    p_name = Lexeme(plugin_name).singular.title().replace("_", "")
    class_name = f"{p_name}{plugin_interface_name}Plugin"

    return class_name


def get_base_class_name(interface):
    """Pass."""
    lex = Lexeme(interface.name).singular.title().replace("_", "")
    base_name = f"Base{lex}Plugin"
    # base_plugin_class = getattr(
    #     getattr(class_based, interface.name),
    #     base_name,
    # )
    return base_name


def load_module(package, relpath):
    """Load a module found at package/relpath.

    Parameters
    ----------
    package: str
        The name of the plugin package that contains module-based plugins.
    relpath: str
        The path to the plugin relative to 'package'.

    Returns
    -------
    module: types.ModuleType
        The loaded module at package.relpath
    """
    # module_name = os.path.splitext(os.path.basename(relpath))[0]
    # We need the full path to the module in order
    # for relative imports to work within modules.
    module_path = os.path.splitext(relpath.replace("/", "."))[0]
    module_path = f"{package}.{module_path}"
    abspath = resources.files(package) / relpath

    spec = util.spec_from_file_location(module_path, abspath)
    module = util.module_from_spec(spec)
    # Import the module
    spec.loader.exec_module(module)

    return module


def get_module_members(module):
    """Get a list of functions, classes, and variables that were implemented in module.

    Parameters
    ----------
    module: types.ModuleType
        The module to gather objects from.

    Returns
    -------
    member_map: dict[list[obj]]
        A dictionary of lists of objects mapped to their object type.
    """
    functions = []
    classes = []
    variables = []

    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj):
            functions.append((name, obj))
        elif inspect.isclass(obj):
            classes.append((name, obj))
        elif inspect.ismodule(obj):
            continue
        else:
            variables.append((name, obj))

    return {"functions": functions, "classes": classes, "variables": variables}


def create_class(module, members, plugin_base_class):
    """Pass."""
    obj_attrs = {}
    for member_type in members:
        if member_type == "classes":
            continue
        else:
            for member_name, member in members[member_type]:
                obj_attrs[member_name] = member

    obj_attrs["__doc__"] = module.__doc__

    # Collect the callable and assign to call
    obj_attrs["call"] = staticmethod(getattr(module, "call"))

    plugin_interface_name = (
        Lexeme(obj_attrs["interface"]).singular.title().replace("_", "")
    )
    plugin_name = Lexeme(obj_attrs["name"]).singular.title().replace("_", "")
    plugin_type = f"{plugin_name}{plugin_interface_name}Plugin"

    # Create an object of type ``plugin_type`` with attributes from ``obj_attrs``
    return type(plugin_type, (plugin_base_class,), obj_attrs)(module)


def module_to_class(interface, package, relpath):
    """Convert a module-based plugin at package/relpath to a class-based plugin.

    Parameters
    ----------
    interface: Object
        The interface object this plugin belongs to.
    package: str
        The name of the plugin package that contains module-based plugins.
    relpath: str
        The path to the plugin relative to 'package'.

    Returns
    -------
    None
    """
    # module_name = os.path.splitext(os.path.basename(relpath))[0]
    module = load_module(package, relpath)

    lex = Lexeme(interface.name).singular.title().replace("_", "")
    base_name = f"Base{lex}Plugin"

    base_plugin_class = getattr(
        getattr(class_based, interface.name),
        base_name,
    )

    member_mapping = get_module_members(module)

    plugin_class = create_class(module, member_mapping, base_plugin_class)

    return plugin_class


def convert_modules_by_package(package):
    """Convert all module plugins in a package that still exist to class-based.

    Parameters
    ----------
    package: str
        The name of the plugin package that contains module-based plugins.

    Returns
    -------
    class_directory: str
        - The directory which contains all of the new class-based plugins.
    """
    for interface_name in interfaces.class_based_interfaces:
        interface = getattr(interfaces, interface_name)
        interface_registry = (
            interface.plugin_registry.registered_class_based_plugins.get(
                interface_name, {}
            )
        )
        for plugin_name, plugin_metadata in interface_registry.items():
            if (
                plugin_metadata.get("is_derived_from_module")
                and plugin_metadata.get("package") == package
            ):
                print(
                    f"Converting {interface_name}'s {plugin_name} to a class-based "
                    "plugin."
                )
                # plugin_class = module_to_class(
                #     interface, package, plugin_metadata.get("relpath")
                # )
                class_name = get_class_name(interface_name, plugin_name)
                base_class_name = get_base_class_name(interface)

                convert_single_file(
                    input_file=str(
                        resources.files(package) / plugin_metadata.get("relpath")
                    ),
                    output_file=(
                        "/home/evan/geoips/geoips_packages/random/"
                        + plugin_metadata.get("relpath").replace(
                            "modules", "classes"
                        )
                    ),
                    class_name=class_name,
                    base_class=base_class_name,
                    interface_name=interface_name,
                )


convert_modules_by_package("geoips")
