from glob import glob
import yaml
import numpy as np
from importlib import metadata, resources, util
import os
import sys

plugins = {}

# schema_yamls = glob(os.getcwd() + "/schema/**/*.yaml", recursive=True)

def get_entry_point_group(group):
    """Get entry point group."""
    if sys.version_info[:3] >= (3, 10, 0):
        return metadata.entry_points(group=group)
    else:
        return metadata.entry_points()[group]

def main():
    plugin_packages = get_entry_point_group("geoips.plugin_packages")
    print(plugin_packages)
    for pkg in plugin_packages:
        package = pkg.value
        print("package == " + str(package))
        pkg_plugin_path = resources.files(package) / "plugins"
        yaml_files = pkg_plugin_path.rglob("*.yaml")
        python_files = pkg_plugin_path.rglob("*.py")
        if package != "geoips":
            schema_yaml_path = resources.files(package) / "schema"
            schema_yamls = schema_yaml_path.rglob("*.yaml")
        else: schema_yamls = []
        plugin_paths = {"yamls": yaml_files, "schemas": schema_yamls, "pyfiles": python_files}
        for interface_key in plugin_paths:
            for filepath in plugin_paths[interface_key]:
                filepath = str(filepath)
                abspath = os.path.abspath(filepath)
                relpath = os.path.relpath(filepath)
                if interface_key == "yamls": # yaml based plugins
                    plugin = yaml.safe_load(open(filepath, mode="r"))
                    interface_name = plugin["interface"]
                    if interface_name not in plugins.keys():
                        plugins[interface_name] = []
                    plugin["abspath"] = abspath
                    plugin["relpath"] = relpath; plugin["package"] = package
                    plugins[interface_name].append(plugin)
                else:
                    if interface_key == "schemas": #schema based yamls
                        split_path = np.array(filepath.split("/"))
                        interface_idx = np.argmax(split_path == "schema") + 1
                        interface_name = split_path[interface_idx]
                        if interface_name not in plugins.keys():
                            plugins[interface_name] = []
                        plugin = yaml.safe_load(open(filepath, mode="r"))
                        plugin["abspath"] = abspath
                        plugin["relpath"] = relpath; plugin["package"] = package
                        plugins[interface_name].append(plugin)
                    else: # module based plugins
                        if "__init__.py" in abspath: continue
                        module_name = str(abspath).split("/")[-1][:-3]
                        spec = util.spec_from_file_location(module_name, abspath)
                        try:
                            module = util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            interface_name = module.interface
                            if interface_name not in plugins.keys():
                                plugins[interface_name] = []
                            family = module.family
                            name = module.name
                            del module
                            module_plugin = {name: {"interface": interface_name, "family": family, "name": name, 
                                                                "abspath": abspath, "relpath": relpath, "package": package}}
                            plugins[interface_name].append(module_plugin)
                        except:
                            continue
    print("Available Plugin Interfaces:\n" + str(plugins.keys()))
    with open("registered_plugins.py", "w") as plugin_registry:
        plugin_registry.write("registered_plugins = {}".format(plugins))

if __name__ == "__main__":
    main()