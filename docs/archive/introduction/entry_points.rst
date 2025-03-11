.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Entry Points for Fun and Profit (well, for Fun at least)
--------------------------------------------------------

One key design aspect of GeoIPS is the requirement to incorporate
external code.  Rather than having a monolithic repository, we
need to be able to make use of algorithms, readers, and products
that are developed by collaborators, and minimize the amount of
work required to integrated them with GeoIPS.  Because the procflows
are part of the main GeoIPS repository, we adopt a plugin approach,
and access the requisite objects via Python's entry point mechanism.

Entry points are most commonly used to automatically set up command
line scripts when Python packages are installed via setuptools.
However, they are also useful in advertising behavior that can be
accessed programmatically.

Entry points are organized into namespaces (it is, after all, Python):
all namespaces for GeoIPS plugins start with "geoips".  Within each
namespace, there is a set of key/value pairs linking a name to a
particular Python object.  Most of the time, this object will be a
function.

For example, the "geoips.readers" namespace contains all of the
readers that are available in a particular Python environment.  Readers
are available from the base GeoIPS install, as well as any other
packages that are configured to advertise readers in the 
"geoips.readers" namespace.

Defining Entry Points
---------------------
Entry points are defined using the setuptools installation method.
In the setup call (populated via a configuration file or a setup.py
file), entry points are defined as a dictionary where the keys are
the namespaces, and the values are lists of strings of key/value pairs:

.. code:: bash
    :number-lines:
    
    setuptools.setup(
        <SNIP>
        entry_points = {
            'console_scripts': [
                'run_procflow=geoips.commandline.run_procflow:main',
            ],
            'geoips.readers': [
                'abi_netcdf=geoips.readers.abi_netcdf:abi_netcdf',
            ],
        },
        <SNIP>
 
In this case, a 'run_procflow' name is added to the 'console_scripts'
entry point namespace, pointing at the function main() in the
geoips.commandline.run_procflow module.  Similarly, the 'abi_netcdf'
reader is advertised in the 'geoips.readers' namespace pointing at
the abi_netcdf() function in the geoips.readers.abi_netcdf module.

Other packages can advertise capability within the geoips namespaces
that point at objects within that package (e.g. a new reader function).

Accessing Entry Points
----------------------
Once entry points are defined, they can be accessed programatically
by name, rather than relying on importation wizardry or searching
the filesystem.  The key module to access the entry points is the
importlib.metadata module - this module provides an entry_points()
function that will retrieve a dictionary of all entry points: the keys
are the string value namespaces, and the values are lists of EntryPoint
objects.

Once this dictionary is obtained, and the proper namespace is accessed,
the constituent entry points can be inspected.  The entry point name
is available via the 'name' attribute of the EntryPoint object.  Once
the correct EntryPoint object is identified, then the EntryPoint's
load() method can be called to instantiate the object.

For example, to find the 'abi_netcdf' reader listed above:

.. code:: bash
    :number-lines:
    
        from importlib import metadata
        for ep in metadata.entry_points()['geoips.readers']:
            if ep.name == 'abi_netcdf':
                abi_netcdf_reader = ep.load()
                break
        else:
            raise Exception('abi_netcdf reader not found!')

Once the entry point is loaded, the object is available for use - for
functions, this means that the function can be called.

Future Reading
--------------
https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
