from glob import glob
import yaml

plugins = {"feature_annotators": {},
           "gridline_annotators": {},
           "product_defaults": {},
           "products": {},
           "sectors": {},
           "bases": {},
           "algorithms": {},
           "colormappers": {},
           "colormaps": {},
           "coverage_checkers": {},
           "filename_formatters": {},
           "interpolators": {},
           "output_formatters": {},
           "procflows": {},
           "readers": {},
           "sector_metadata_generators": {},
           "sector_spec_generators": {},
           "title_formatters": {},
           }

plugin_paths = {"plugins.yaml.feature_annotators": glob(".plugins/yaml/feature_annotators/*.yaml"),
                "plugins.yaml.gridline_annotators": glob("./plugins/yaml/gridline_annotators/*.yaml"),
                "plugins.yaml.product_defaults": glob("./plugins/yaml/product_defaults/**/*.yaml", recursive=True),
                "plugins.yaml.products": glob("./plugins/yaml/products/*.yaml"),
                "plugins.yaml.sectors": glob("./plugins/yaml/sectors/**/*.yaml", recursive=True),
                "plugins.modules.algorithms": glob("./plugins/modules/algorithms/**/*.py", recursive=True),
                "plugins.modules.colormappers": glob("./plugins/modules/colormappers/**/*.py", recursive=True),
                "plugins.modules.colormaps": glob("./plugins/modules/colormaps/**/*.py", recursive=True),
                "plugins.modules.coverage_checkers": glob("./plugins/modules/coverage_checkers/**/*.py", recursive=True),
                "plugins.modules.filename_formatters": glob("./plugins/modules/filename_formatters/**/*.py", recursive=True),
                "plugins.modules.interpolators": glob("./plugins/modules/interpolators/**/*.py", recursive=True),
                "plugins.modules.output_formatters": glob("./plugins/modules/output_formatters/**/*.py", recursive=True),
                "plugins.modules.procflows": glob("./plugins/modules/procflows/**/*.py", recursive=True),
                "plugins.modules.readers": glob("./plugins/modules/readers/**/*.py", recursive=True),
                "plugins.modules.sector_metadata_generators": glob("./plugins/modules/sector_metadata_generators/**/*.py", recursive=True),
                "plugins.modules.sector_spec_generators": glob("./plugins/modules/sector_spec_generators/**/*.py", recursive=True),
                "plugins.modules.title_formatters": glob("./plugins/modules/title_formatters/**/*.py", recursive=True),
                "schema.bases": glob("./schema/bases/*.yaml"),
                "schema.feature_annotators": glob("./schema/feature_annotators/*.yaml"),
                "schema.gridline_annotators": glob("./schema/gridline_annotators/*.yaml"),
                "schema.product_defaults": glob("./schema/product_defaults/**/*.yaml", recursive=True),
                "schema.products": glob("./schema/products/**/*.yaml", recursive=True),
                "schema.sectors": glob("./schema/sectors/*.yaml"),
                }

for interface_key in plugin_paths:
    interface_name = interface_key.split(".")[-1]
    for filepath in plugin_paths[interface_key]:
        if interface_key.split(".")[0] == "plugins" and filepath[-4:] == "yaml":
            plugin = yaml.safe_load(open(filepath, mode="r"))
            name = plugin["name"]
            family = plugin["family"]
            docstring = plugin["docstring"]
            plugins[interface_name][name] = {"family": family, "docstring": docstring}
        elif filepath[-4:] == "yaml": #schema yaml files
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
            import_str = "from geoips.plugins.modules." + interface_name
            entry_points = filepath.split("/")
            if interface_name == entry_points[-2]:
                import_str += " import " + entry_points[-1][0:-3]
            else:
                import_str += "." + entry_points[-2] + " import " + entry_points[-1][0:-3]
            plugins[interface_name][entry_points[-1][0:-3]] = {"import_string": import_str}

print(plugins)