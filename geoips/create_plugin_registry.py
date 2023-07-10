from glob import glob
import yaml
import numpy as np
import importlib
from importlib import metadata
import os
import sys

plugins = {}

plugin_paths = {"plugins.yamls": glob("./plugins/yaml/**/*.yaml", recursive=True),
                "plugins.modules": glob("./plugins/modules/**/*.py", recursive=True),
                "schema.yamls": glob("./schema/**/*.yaml", recursive=True),
                }

def get_entry_point_group(group):
    """Get entry point group."""
    if sys.version_info[:3] >= (3, 10, 0):
        return metadata.entry_points(group=group)
    else:
        return metadata.entry_points()[group]

def main():
    plugin_packages = get_entry_point_group("geoips.plugin_packages")
    package = plugin_packages[0].value
    for interface_key in plugin_paths:
        for filepath in plugin_paths[interface_key]:
            abspath = os.path.abspath(filepath)
            relpath = os.path.relpath(filepath)
            if interface_key.split(".")[0] == "plugins" and interface_key.split(".")[-1] == "yamls":
                plugin = yaml.safe_load(open(filepath, mode="r"))
                interface_name = plugin["interface"]
                if interface_name not in plugins.keys():
                    plugins[interface_name] = []
                plugin["abspath"] = abspath
                plugin["relpath"] = relpath; plugin["package"] = package
                plugins[interface_name].append(plugin)
            else:
                if interface_key.split(".")[0] == "schema": #schema yaml files
                    split_path = np.array(filepath.split("/"))
                    interface_idx = np.argmax(split_path == "schema") + 1
                    interface_name = split_path[interface_idx]
                    if interface_name not in plugins.keys():
                        plugins[interface_name] = []
                    plugin = yaml.safe_load(open(filepath, mode="r"))
                    plugin["abspath"] = abspath
                    plugin["relpath"] = relpath; plugin["package"] = package
                    plugins[interface_name].append(plugin)
                else:
                    if "__init__.py" in filepath: continue
                    split_path = np.array(filepath.split("/"))
                    interface_idx = np.argmax(split_path == "modules") + 1
                    import_str = "plugins.modules"
                    for folder in split_path[interface_idx: -1]:
                        import_str += "." + folder
                    filename = split_path[-1][0:-3]
                    import_str += "." + filename
                    try:
                        module = importlib.import_module(import_str)
                        interface_name = module.interface
                        if interface_name not in plugins.keys():
                            plugins[interface_name] = []
                        family = module.family
                        name = module.name
                        del module
                        module_plugin = {name: {"interface": interface_name, "family": family, "name": name, 
                                                            "abspath": abspath, "relpath": relpath, "package": package}}
                        plugins[interface_name].append(module_plugin)
                    except Exception as e:
                        continue
    print("Available Plugin Interfaces:\n" + str(plugins.keys()))
    with open("registered_plugins.py", "w") as plugin_registry:
        plugin_registry.write("registered_plugins = {}".format(plugins))

if __name__ == "__main__":
    main()