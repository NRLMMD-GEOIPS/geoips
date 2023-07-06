from glob import glob
import yaml
import numpy as np
import importlib

plugins = {}

plugin_paths = {"plugins.yamls": glob("./plugins/yaml/**/*.yaml", recursive=True),
                "plugins.modules": glob("./plugins/modules/**/*.py", recursive=True),
                "schema.yamls": glob("./schema/**/*.yaml", recursive=True),
                }

def main():
    for interface_key in plugin_paths:
        for filepath in plugin_paths[interface_key]:
            if interface_key.split(".")[0] == "plugins" and interface_key.split(".")[-1] == "yamls":
                plugin = yaml.safe_load(open(filepath, mode="r"))
                interface_name = plugin["interface"]
                if interface_name not in plugins.keys():
                    plugins[interface_name] = {}
                name = plugin["name"]
                family = plugin["family"]
                docstring = plugin["docstring"]
                plugins[interface_name][name] = {"family": family, "docstring": docstring}
            else:
                if interface_key.split(".")[0] == "schema": #schema yaml files
                    split_path = np.array(filepath.split("/"))
                    interface_idx = np.argmax(split_path == "schema") + 1
                    interface_name = split_path[interface_idx]
                    if interface_name not in plugins.keys():
                        plugins[interface_name] = {}
                    plugin = yaml.safe_load(open(filepath, mode="r"))
                    id = plugin["$id"]
                    yaml_type = None
                    description = None
                    try:
                        description = plugin["description"]
                        yaml_type = plugin["type"]
                        plugins[interface_name][id] = {"type": yaml_type, "description": description}
                    except Exception:
                        plugins[interface_name][id] = {"type": yaml_type, "description": description}
                else:
                    if "__init__.py" in filepath: continue
                    split_path = np.array(filepath.split("/"))
                    interface_idx = np.argmax(split_path == "modules") + 1
                    import_str = "plugins.modules"
                    for folder in split_path[interface_idx: -1]:
                        import_str += "." + folder
                    filename = split_path[-1][0:-3]
                    import_str += "." + filename
                    module = importlib.import_module(import_str)
                    try:
                        interface_name = module.interface
                        if interface_name not in plugins.keys():
                            plugins[interface_name] = {}
                        family = module.family
                        name = module.name
                        plugins[interface_name][filename] = {"family": family, "name": name}
                    except Exception as e:
                        continue
    print("Avalable plugin keys:\n" + str(plugins.keys()))
    with open("registered_plugins.py", "w") as plugin_registry:
        plugin_registry.write("registered_plugins = {}".format(plugins))
    # return plugins

if __name__ == "__main__":
    main()