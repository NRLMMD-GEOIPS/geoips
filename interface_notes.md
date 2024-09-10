    # # # This source code is protected under the license referenced at
    # # # https://github.com/NRLMMD-GEOIPS.

# What I'm doing
As part of developing a CLI, I'm trying to standardize the interfaces. To do this, I'll impelement the following:
- `interfaces.BaseInterface`: A base class for interfaces with appropriate functions
  - This is complete other than `is_valid` which will need to call `is_valid` from a plugin's family.
- `interfaces.BaseYamlInterface`: A base class for interfaces that make use of YAML configuration
  - Not started
- `interfaces.BaseFamily`: A base class for plugin families
  - Not started
  - Currently, this would implement a single method, `is_valid`.
  - `is_valid` would require that sublcasses set `cls.required_args` and `cls.required_kwargs` as lists of arguments
    that are required in the call signature.
- `interfaces.BaseYamlFamily`: A base class for YAML plugin families
  - Not Started
  - Currently, this would implement a single method, `is_valid`.
  - `is_valid` would validate yaml against some kind of schema that would be set in `cls.yaml_schema`.

# Status
- I have created a base interface class for all non-yaml-based plugins. The `BaseInterface` class implements several
  functions:
  - is_valid: Tests a specific plugin's call signature
  - get: Gets a named plugin's callable
  - get_plugin_attr: Gets a named attribute from a named plugin
  - get_family: Gets the family attribute
  - get_description: Gets a named plugin's description attribute
  - get_list: Gets a list of available plugins for the interface
  - test_interface_plugins: Runs is_valid for all of an interface's plugins
- Migrated all non-yaml-config interfaces to use `BaseInterface`
  - These are located in `geoips/interfaces`
  - Migrated so far include:
    - `algorithms`
    - `colormaps`
    - `filename_formatters`
    - `interpolators`
    - `output_formats`
    - `procflows`
    - `readers`
    - `title_formatters`
- Still need to create `BaseYamlInterface`
- Migrate yaml-config interfaces to use `BaseYamlInterface`
  - `procflow_configs`
  - `boundary_configs`
  - `gridline_configs`
- Still need to implement Families
  - Create `BaseFamily` class
  - Create subclasses for each family for each interface
- Need to remove old interfaces
- Update geoips_overview.rst
- Update available_functionality.rst
- Update list_available_modules.py
- Examine other commandline scripts


# Before First PR
- Drop `dev` and `stable` for interfaces that I've reimplemented.
- Update `interface_modules` to be `plugins`, then update the directory names to match the new naming structure.
- Can get rid of `test_interfaces` and `list_available_modules` from `commandline` now.
  - Borrow some functionality from `test_interfaces`.
- Need to reimplement is_valid to actually check the call signature.
- Run tests
  - amsr2
  - goes16
  - recenter tc


```python
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in pmw_tb.pmw_89pct, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in pmw_tb.pmw_color37, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in pmw_tb.pmw_color89, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in sfc_winds.windbarbs, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in single_channel, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in visir.Night_Vis, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in visir.Night_Vis_GeoIPS1, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in visir.Night_Vis_IR, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
/Users/jsolbrig/NRL/geoips_packages/geoips/geoips/dev/alg.py:202: DeprecationWarning: Algorithm attribute "alg_func_type", used in visir.Night_Vis_IR_GeoIPS1, is deprecated and will be removed in a future release. Please replace all occurrences with "func_type".
  warn(msg, DeprecationWarning, stacklevel=1)
[26, 19, 59]
name                       | type                | description
--------------------------------------------------------------------------------------------------------------
pmw_tb.pmw_37pct           | list_numpy_to_numpy | Passive Microwave 37 GHz Polarization Corrected Temperature
pmw_tb.pmw_89pct           | list_numpy_to_numpy |
pmw_tb.pmw_color37         | list_numpy_to_numpy |
pmw_tb.pmw_color89         | list_numpy_to_numpy |
sfc_winds.windbarbs        | list_numpy_to_numpy |
single_channel             | list_numpy_to_numpy |
visir.Night_Vis            | list_numpy_to_numpy |
visir.Night_Vis_GeoIPS1    | list_numpy_to_numpy |
visir.Night_Vis_IR         | list_numpy_to_numpy |
visir.Night_Vis_IR_GeoIPS1 | list_numpy_to_numpy |
```

# Important to do for review
- ~~Ensure that the output of alg.get_list(by_type=True) fits what it was before. Something doesn't look right.~~
  - I think I have this fixed. Still worth checking, but it doesn't look like this interface was working correctly anyway!

# Questions
- Need to figure out what we want to call `Boundaries` and `Gridlines` which are both yaml-config based. These likely
  shouldn't be combined into a single class because they are sometimes mixed and matched.
  - Maybe have a MapInterface module that defines which Boundaries and Gridlines you want to use.
- It looks like the `output_config` interface implements `get_output_format` and `get_output_format...`. These need to
  be updated to work better with the new system and have appropriate names.
- What is the difference between `geoips/dev/utils.py` and `geoips/geoips_utils.py`? It seems like a lot of what is in
  dev should just be moved to the top-level module?
- Should each of the interfaces have `geoips test <interface>` in the CLI?
  - For example, for algorithms, this would call `algs.test_alg_interface()` and would look like `geoips test
    algorithms`
  - This would allow a user/developer to automatically test any new plugins that they've added to be sure that they're
    working correctly with GeoIPS
- What is `get_remove_duplicates_func()` in filename.py and title.py?
- One advantage to using classes rather than modules for interface modules would be the ability to deprecate old
  behavior. For example, currently, if I want to deprecate the use of `alg_func_type` in favor of `func_type` it becomes
  fairly difficult. With a base class, this kind of thing would be relatively easy. I'm sure that there are some
  significant disadvantages here, too, though. Just thinking.


# Interfaces
## Bases
### BaseInterface
Used to define the majority of the interface functions.
- is_valid
  - Will make use of families to validate plugins
- get
  - Returns a callable for a specific plugin
- get_family
  - Returns the name of the family for a named plugin
- get_list
  - Lists all of the plugins available for a given interface
- test_interface
  - Runs is_valid for all plugins for the interface

## Migrated
### ~~algs - Moved to interfaces as `algorithms`~~
- is_valid_alg(alg_func_name) -> is_vaild(func_name)
  - ~~Only here in test interface~~
- get_alg(alg_func_name) -> get(func_name)
  - ~~geoips/interface_modules/single_source.py~~
- get_alg_type(alg_func_name) -> get_family(func_name)
  - ~~geoips/dev/product.py~~
    - ~~I think this could be dropped. It is part of an error-handling if statement that I don't think really requires
      the algorithm type. It should be enough to say that the algorithm being run does not have `output_data_range`.~~
  - ~~geoips/interface_modules/single_source.py~~
    - I think we're stuck with this, but maybe worth examining
- list_algs_by_type -> get_list
  - geoips/commandline/list_available_modules.py
    - Needed for backwards compatability but should be deprecated
    - Also requires by_type=True for now...
- test_alg_interface -> test_interface
  - Only here
  - ***Needs testing to ensure that get_list(by_type=True) works the same as before. Something looks funny!***
- ~~Add get_description~~
### ~~cmap - Moved to interfaces as `colormaps`~~
- is_valid_cmap(cmap_func_name)
  - ~~Only here~~
- get_cmap(cmap_func_name)
  - available_functionality.rst
  - ~~geoips/dev/output_config.py~~
  - ~~geoips/dev/product.py~~
  - ~~geoips/image_utils/colormap_utils.py~~
    - This is actually matplotlib.cm.get_cmap, not ours
  - ~~geoips/interface_modules/procflows/single_source.py~~
  - ~~geoips/interface_modules/user_colormaps/matplotlib_linear_norm.py~~
    - This is actually matplotlib.cm.get_cmap, not ours
- get_cmap_type(cmap_func_name)
  - ~~Only here~~
- list_cmaps_by_type
  - geoiops/commandline/list_available_modules.py
- test_cmap_interface
  - ~~Only here~~
- ~~Add get_description~~
### filenames - Moved to interfaces as `filename_formatters`
- is_valid_filenamer(filename_func_type)
  - ~~Only here~~
- *get_remove_duplicates_func(filename_func_name)*
  - Only here
  - This does need to be handled, but I think it needs to be handled differently.
    - Add `find_duplicates` function
- get_filenamer(filename_func_name)
  - ~~geoips/filenames/duplicate_files.py~~
  - ~~geoips/interface_modules/filename_formats/geotiff_fname.py~~
  - ~~geoips/interface_modules/filename_formats/tc_clean_filename.py~~
  - ~~geoips/interface_modules/procflows/single_source.py~~
- get_filenamer_type(func_name)
  - ~~geoips/interface_modules/procflows/single_source.py~~
- list_filenamers_by_type
  - geoiops/commandline/list_available_modules.py
- test_filename_interface
  - ~~Only here~~
- ~~Add get_description~~
### ~~interp - Moved to interfaces as `interpolators`~~
- is_valid_interp(interp_func_name)
  - ~~Only here~~
- get_interp(interp_func_name)
  - ~~geoips/interface_modules/coverage_checks/windbarbs.py~~
  - ~~geoips/interface_modules/procflows/config_based.py~~
  - ~~geoips/interface_modules/procflows/single_source.py~~
- get_interp_type(interp_func_name)
  - ~~Only here~~
- list_interps_by_type
  - geoiops/commandline/list_available_modules.py
- test_interp_interface
  - ~~Only here~~
- Add get_description
### ~~output - Normal~~
- is_valid_outputter(output_func_name)
  - ~~Only here~~
- get_outputter(output_func_name)
  - ~~geoips/interface_modules/procflows/config_based.py~~
  - ~~geoips/interface_modules/procflows/single_source.py~~
- get_outputter_type(output_func_name)
  - ~~geoips/interface_modules/procflows/config_based.py~~
  - ~~geoips/interface_modules/procflows/single_source.py~~
- list_outputters_by_type
  - geoiops/commandline/list_available_modules.py
- test_output_interface
  - ~~Only here~~
- Add get_description
### ~~procflow - Normal~~
- is_valid_procflow(procflow_func_name)
  - ~~Only here~~
- get_procflow(procflow_func_name)
  - ~~geoips/commandline/run_procflow.py~~
- get_procflow_type(procflow_func_name)
  - ~~Only here~~
- list_procflows_by_type
  - geoiops/commandline/list_available_modules.py
- test_procflow_interface
  - ~~Only here~~
- Add get_description
### ~~readers - Moved to interfaces as `readers`~~
- is_valid_reader(reader_name) -> is_valid(reader_name)
  - ~~Only here~~
- get_reader(reader_name) -> get(reader_name)
  - available_functionality.rst
  - ~~geoips/interface_modules/procflows/config_based.py~~
  - ~~geoips/interface_modules/procflows/single_source.py~~
- get_reader_type(reader_name) -> get_family(reader_name)
  - ~~Only here~~
- list_readers_by_type() -> get_list(by_family=True)
  - geoips_overview.rst
  - geoips/commandline/list_available_modules.py
- test_reader_interface() -> test_interface()
  - geoips_overview.rst
### ~~title - Normal~~
- is_valid_title(title_func_name)
  - ~~Only here~~
- *get_remove_duplicates_func(title_func_name)*
  - ~~Only here~~
- get_title(title_func_name)
  - ~~geoips/image_utils/mpl_utils.py~~
- get_title_type(func_name)
  - ~~Only here~~
- list_titles_by_type
  - ~~Only here~~
- test_title_interface
  - ~~Only here~~
- Add get_description

## To Migrate
### boundaries - **Requires BaseYamlInterface**
- is_valid_boundaries(boundaries_name)
  - Only here
- get_boundaries(boundaries_name)
  - geoips/dev/output_config.py
- get_boundaries_type(boundaries_name)
  - Only here
- list_boundaries_by_type
  - geoips/commandline/list_available_modules.py
- test_boundaries_interface
  - Only here
- Add get_description
### gridlines - **Requires BaseYamlInterface**
- is_valid_gridlines(gridlines_name)
  - Only here
- get_gridlines(gridlines_name)
  - geoips/dev/output_config.py
  - geoips/interface_modules/procflows/single_source.py
- *set_lonlat_spacing(gridlines_info, area_def)*
  - geiops/dev/output_config.py
- get_gridlines_type(gridlines_name)
  - Only here
- list_gridlines_by_type
  - geoiops/commandline/list_available_modules.py
- test_gridlines_interface
  - Only here
- Add get_description
### output_config - **This may be more complicated than the others**
- is_valid_output_config(output_config_dict)
  - Only here
- get_output_config_type(outout_config_dict)
  - Only here
- *get_filename_formats(output_dict)*
  - geoips/interface_modules/procflows/single_source.py
- *get_output_format(output_dict)*
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.py
- *get_metadata_output_format(output_dict)*
  - geoips/interface_modules/procflows/single_source.py
- *get_metadata_filename_format(filename_format, output_dict)*
  - geoips/interface_modules/procflows/single_source.py
- *get_minimum_coverage(product_name, output_dict)*
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.py
- *get_filename_format_kwargs(filename_format, output_dict)*
  - geoips/interface_modules/procflows/single_source.py
- *get_metadata_filename_format_kwargs(filename_format, output_dict)*
  - geoips/interface_modules/procflows/single_source.py
- *get_output_format_kwargs(output_dict, xarray_obj=None, area_def=None, sector_type=None)*
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.py
- *get_metadata_output_format_kwargs(output_dict)*
  - geoips/interface_modules/procflows/single_source.py
- *produce_current_time(config_dict, metadata_xobj, output_dict_keys=None)*
  - geoips/interface_modules/procflows/config_based.py
- tests_output_config_interface(output_config_dict)
  - Only here
- Add get_description
### product - **I think this is more similar to BaseInterface but need to look more closely**
- is_valid_product(product_name, source_name, output_dict=None)
  - Only here
- get_product(product_name, source_name, output_dict=None)
  - available_functionality.rst
  - geoips/interface_modules/output_formats/imagery_annotated.py
- get_product_type(product_name, source_name)
  - geoips/interface_modules/procflows/single_source.py
- list_products_by_type
  - geoiops/commandline/list_available_modules.py
- list_products_by_source
  - geoips/dev/cmap.py (commented out)
  - geoips/dev/interp.py (commented out)
- list_products_by_product
  - Only here
- list_products
  - Only here
- get_source_inputs(source_name)
  - Only here
- get_product_specs(product_name)
  - Only here
- test_product_interface
  - Only here
- get_alg_name(product_name, source_name, output_dict=None)
  - geoips/interface_modules/procflows/single_source.py
- get_alg_args(product_name, source_name, output_dict=None)
  - geoips/interface_modules/procflows/single_source.py
- get_required_variables(product_name, source_name, output_dict=None)
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.py
- get_requested_datasets_for_variables(product_name, source_name, output_dict=None)
  - geoips/interface_modules/procflows/single_source.py
- get_data_range(product_name, source_name, output_dict=None)
  - Only here
- get_interp_name(product_name, source_name, output_dict=None)
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.py
- get_interp_args(product_name, source_name, output_dict=None)
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.py
- get_product_display_name(product_name, source_name, output_dict=None)
  - geoips/interface_modules/procflows/single_source.py
- get_cmap_name(product_name, source_name, output_dict=None)
  - geoips/dev/cmap.py
  - geoips/dev/output_config.py
  - geoips/interface_modules/procflows/single_source.py
- get_cmap_args(product_name, source_name, output_dict=None)
  - geoips/dev/cmap.py
  - geoips/dev/output_config.py
  - geoips/interface_modules/procflows/single_source.py
- get_cmap_from_product(product_name, source_name, output_dict=None)
  - geoips/dev/cmap.py
- get_covg_from_product(product_name, source_name, output_dict=None)
  - geoips/interface_modules/output_formats/imagery_annotated.py
  - geoips/interface_modules/output_formats/metadata_tc.py
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.py
- get_covg_args_from_product(product_name, source_name, output_dict=None)
  - geiops/interface_modules/filename_formats/utils/tc_file_naming.py
  - geoips/interface_modules/output_formats/imagery_annotated.py
  - geoips/interface_modules/output_formats/metadata_tc.py
  - geoips/interface_modules/procflows/config_based.py
  - geoips/interface_modules/procflows/single_source.,py
- Add get_description
