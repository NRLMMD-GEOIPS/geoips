# GeoIPS Yaml-based Plugin Options
Internally, we would like Plugins to behave the same, regardless of whether they are Module-based or Yaml-based. This
means that we would like to automatically discover Plugins of both types and automatically create Python objects for
each Plugin. This will allow them to share functionality without needing to duplicate code.

## Current Situation

### Module-based Plugins
At present, we have updated GeoIPS to automatically discover and objectify Module-based plugins. This is achieved by
implementing a class for each GeoIPS Interface and a second class for Plugins associated with each interface. Classes
include:
- `BaseInterface` and `BaseInterfacePlugin`: Base classes which should not be instantiated directly.
- `AlgorithmsInterface` and `AlgorithmsInterfacePlugin`: Classes for the algorithms interface and algorithm plugins.
- `ReadersInterface` and `ReadersInterfacePlugin`
- `ColorMapsInterface` and `ColorMapsInterfacePlugin`
- etc...

Plugins of these types are discovered by referencing entry points defined in a package's `setup.py`. These look like
this:
```python
setup(
    ...
    entry_points={
        'geoips.readers': [
            'abi_netcdf=geoips.interface_modules.readers.abi_netcdf:abi_netcdf',
            'abi_l2_netcdf=geoips.interface_modules.readers.abi_netcdf:abi_l2_netcdf',
            ...
        ],
        'geoips.algorithms': [
            'single_channel=geoips.interface_modules.algorithms.single_channel:single_channel',
            'pmw_tb.pmw_37pct=geoips.interface_modules.algorithms.pmw_tb.pmw_37pct:pmw_37pct',
            ...
        ]
    }
)
```

From this, for example, `abi_netcdf` would be turned into an object of type `ReadersInterfacePlugin`. When creating the
object, GeoIPS will interpret the `abi_netcdf` line as:
```
abi_netcdf=geoips.interface_modules.readers.abi_netcdf:abi_netcdf
{plugin_name}={package_name}.{module}:{plugin_function}
```
- **Left Side**: The name of the plugin (`plugin_name`). This is the name that the plugin is registered to within GeoIPS.
  - For the `abi_netcdf` reader, if `reader` is an object of type `ReadersInterfacePlugin`, `print(reader.name)` would
    return `"abi_netcdf"`.
- **Right Side**: Composed of multiple parts
  - `package_name`: Indicates which package the plugin comes from. Can be something other than `geoips` to register an
    interface from an external package.
  - `module`: The path, within `package_name`, to a module that contains the plugin.
  - `plugin_function`: The name of the function that should be called when using the plugin.
    - In the future this should be `main` to provide consistency between packages. For now, functions other than `main`
      will raise a `DeprecationWarning`.

### Yaml-based Plugins
Yaml-based Plugins don't work the way that we would like and are blocking us from being able to install
GeoIPS packages like "normal" Python packages. We don't have a good discovery mechanism for Yaml-based Plugins and
`setup.py` doesn't provide a good mechanism that we can make use of like `entry_points`.

Right now, we rely on GeoIPS-related packages being installed in a specific directory specified by the
`GEOIPS_PACKAGES_DIR` environment variable. This allows us to search all of the GeoIPS-related packages for YAML files
that fall in a particular directory structure.

## Ideas
1. Use `entry_points` to point to GeoIPS-related packages, then use an **enforced** directory structure to guide plugin
   discovery. `setup.py` would just reference the top-level plugin packages:
   ```python
   setup(
       entry_points={
           'geoips.packages': [
               'myplugin=myplugin',  # Just point to the plugin package
           ]
       }
   )
   ```
   Plugins would be found by looking through the directory structure of each package where the directory structure must
   **exactly** follow the GeoIPS requirements:
   ```
   myplugin/
     plugins/
       readers/
         abi_netcdf.py
       algorithms/
         pmw_tb/pmw_37pct.py
       boundaries/
         default.yaml
    ```

    **Pros:**
    - Creating plugins would only require creating the appropriate Plugin Module or the appropriate YAML file.
    - No additional files are required.
    - No special `entry_points` are required other than registring your package as shown above.

    **Cons:**
    - Does not allow specification of plugin locations.
    - Breaks some backwards compatability (e.g. plugin functions named something other than `main`).

2. Require a Python wrapper for each Yaml-based Plugin.

   Say that we have a plugin that looks like this:
   ```
   myplugin/
     plugins/
       plotting_params/
         boundaries/
           myboundaries.yaml
   ```
   We would need to add a python wrapper that looks like this:
   ```python
   import yaml

   with open('myboundaries.yaml') as df:
       myboundaries = yaml.safe_load(df)
   ```
   Where the directory structure would look like this:
   ```
   myplugin/
     plugins/
       plotting_params/
         boundaries/
           myboundaries.py
           myboundaries.yaml
   ```
   This could then be added to `entry_points` like this:
   ```python
   setup(
       entry_points={
           'geoips.boundaries': [
               'myboundaries=myplugin.plugins.plotting_params.boundaries.myboundaries:myboundaries',
           ]
       }
   )
   ```

   **Pros:**
   - Is more explicit. Less magic.

   **Cons:**
   - Requires an extra file for every yaml-based plugin.

3. Create a top-level configuration file for GeoIPS packages

   Using the same example as above, but leaving off the Python package, we could create a top-level configuration file
   where we would list our plugins. It would then import and run a wrapper from the main GeoIPS package.

   ```python
   from geoips.utils import register_plugin

   yaml_plugins = [
       './plugins/plotting_params/boundaries/myboundaries.yaml',
   ]

   for plugin_file in yaml_plugins:
       register_plugin(plugin_file)
   ```


   **Pros:**
   - Relatively explicit. A little magic.
   - Only requires one extra file per plugin package (can contain multiple plugins)

   **Cons:**
   - Not entirely explicit.
   - Requires an extra file that is very GeoIPS-specific.