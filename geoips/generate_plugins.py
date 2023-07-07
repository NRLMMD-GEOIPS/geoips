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
                plugins[interface_name][name] = {"interface": interface_name, "family": family, "name": name, "docstring": docstring}
            else:
                if interface_key.split(".")[0] == "schema": #schema yaml files
                    split_path = np.array(filepath.split("/"))
                    interface_idx = np.argmax(split_path == "schema") + 1
                    interface_name = split_path[interface_idx]
                    if interface_name not in plugins.keys():
                        plugins[interface_name] = {}
                    plugin = yaml.safe_load(open(filepath, mode="r"))
                    id = None
                    yaml_type = None; description = None; ref = None; title = None
                    for arg in range(5):
                        try:
                            if arg == 0: id = plugin["$id"]
                            elif arg == 1: yaml_type = plugin["type"]
                            elif arg == 2: ref = plugin["$ref"]
                            elif arg == 3: title = plugin["title"]
                            elif arg == 4: description = plugin["description"]
                        except Exception:
                            continue 
                    plugins[interface_name][id] = {"name": id, "type": yaml_type, 
                                                   "ref": ref, "title": title, "description": description}
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
                            plugins[interface_name] = {}
                        family = module.family
                        name = module.name
                        plugins[interface_name][filename] = {"interface": interface_name, "family": family, "name": name}
                    except Exception as e:
                        continue
    print("Avalable plugin keys:\n" + str(plugins.keys()))
    with open("registered_plugins.py", "w") as plugin_registry:
        plugin_registry.write("registered_plugins = {}".format(plugins))

if __name__ == "__main__":
    main()