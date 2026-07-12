.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

 This source code is subject to the license referenced at
 https://github.com/NRLMMD-GEOIPS.

.. _configuration:

Configuring GeoIPS
******************

GeoIPS supports configuring your environment through two complementary mechanisms:

1. **Configuration file** (``.geoips.yaml``) — A project-level YAML file that
   defines all settings in one place. This is the recommended approach.
2. **Environment variables** — Individual ``GEOIPS_*`` variables that override
   specific settings. Ideal for CI/CD, containers, or temporary overrides.

When both are used, environment variables always take precedence over the
configuration file.

Configuration File
==================

GeoIPS ships with sensible defaults for every setting. You can override any
of these defaults by creating a project-level ``.geoips.yaml`` file.

File format
-----------

The configuration file uses a nested YAML structure under the top-level
``geoips:`` key:

.. code-block:: yaml

    # .geoips.yaml
    geoips:
      outdirs: /data/geoips_output
      features:
        no_color: true
        rebuild_registries: false
      cache:
        geolocation_cache_backend: zarr
      logging:
        level: debug
      test:
        output_checker_threshold_image: 0.10

Most keys are optional — only specify the ones you want to override. The one
setting you should provide is ``outdirs`` (equivalently ``GEOIPS_OUTDIRS``),
which controls where GeoIPS writes output. If it is not set via the environment
or the configuration file, GeoIPS logs a warning and falls back to
``$HOME/geoips_outdirs``.

Search locations
----------------

GeoIPS searches for a project configuration file in the following order,
using the first file found:

1. ``$GEOIPS_RCFILE`` — Path set by the environment variable (if defined
   and the file exists).
2. ``./.geoips.yaml`` — In the current working directory.
3. ``~/.config/geoips/config.yaml`` — In the user's XDG-compliant
   configuration directory.

Configuration priority
----------------------

Settings are resolved with this priority (highest wins):

1. **Environment variables** — ``GEOIPS_*`` and unprefixed aliases
   (``NO_COLOR``, ``BOXNAME``, ``DEFAULT_QUEUE``).
2. **Project ``.geoips.yaml`` file** — Found via the search locations above.
3. **Built-in defaults** — Sensible values shipped with the code.

For example, setting ``GEOIPS_LOGGING_LEVEL=debug`` in your environment
will override whatever is set in your ``.geoips.yaml`` file.

Accessing configuration in Python
---------------------------------

The configuration is available as a singleton via ``geoips.config``:

.. code-block:: python

    from geoips.config import config

    # Dot-attribute access (recommended)
    print(config.outdirs)
    print(config.features.no_color)
    print(config.cache.geolocation_cache_backend)

    # Dict-style access (backward compatible, deprecated)
    print(config["GEOIPS_OUTDIRS"])
    print(config["NO_COLOR"])

.. note::

   The legacy ``geoips.filenames.base_paths.PATHS`` dictionary is
   deprecated but still functional. It forwards to the new configuration
   system and emits a ``DeprecationWarning`` on import. Update existing
   code to use ``from geoips.config import config`` instead.

Settings reference
------------------

The table below lists all configurable settings, their YAML paths, and
their corresponding environment variable names.

.. note::

   :data:`geoips.config.schema.GEOIPS_ENV_MAP` is the authoritative,
   canonical mapping of every supported environment variable to its
   configuration setting. The tables below are a human-readable reference
   generated from that map. A unit test
   (``tests/unit_tests/config/test_env_map_sync.py``) enforces that the
   map, the schema, and the legacy ``base_paths.py`` variables stay in
   sync, so any newly added setting must be registered in ``GEOIPS_ENV_MAP``.

.. list-table:: Configuration Settings Reference
   :header-rows: 1
   :widths: 30 35 20 15

   * - Setting
     - YAML Path
     - Env Variable
     - Default
   * - Output directory
     - ``geoips.outdirs``
     - ``GEOIPS_OUTDIRS``
     - ``$HOME/geoips_outdirs``
   * - Packages directory
     - ``geoips.packages_dir``
     - ``GEOIPS_PACKAGES_DIR``
     - auto (source tree)
   * - Base directory
     - ``geoips.basedir``
     - ``GEOIPS_BASEDIR``
     - auto (source tree)
   * - Test data directory
     - ``geoips.testdata_dir``
     - ``GEOIPS_TESTDATA_DIR``
     - ``$basedir/test_data``
   * - Dependencies directory
     - ``geoips.dependencies_dir``
     - ``GEOIPS_DEPENDENCIES_DIR``
     - ``$basedir/geoips_dependencies``
   * - Cache directory
     - ``geoips.cache.cache_dir``
     - ``GEOIPS_CACHE_DIR``
     - ``platformdirs.user_cache_dir``
   * - Data cache directory
     - ``geoips.cache.data_cache_dir``
     - ``GEOIPS_DATA_CACHE_DIR``
     - ``$outdirs/cache/geoips``
   * - Satpy cache directory
     - ``geoips.cache.satpy_data_cache_dir``
     - ``SATPY_DATA_CACHE_DIR``
     - ``$outdirs/cache/satpy``
   * - Cache backend
     - ``geoips.cache.geolocation_cache_backend``
     - ``GEOIPS_GEOLOCATION_CACHE_BACKEND``
     - ``memmap``
   * - Disable color output
     - ``geoips.features.no_color``
     - ``NO_COLOR``
     - ``false``
   * - Use pydantic validation
     - ``geoips.features.use_pydantic``
     - ``GEOIPS_USE_PYDANTIC``
     - ``false``
   * - Rebuild registries
     - ``geoips.features.rebuild_registries``
     - ``GEOIPS_REBUILD_REGISTRIES``
     - ``true``
   * - Operational user mode
     - ``geoips.features.operational_user``
     - ``GEOIPS_OPERATIONAL_USER``
     - ``false``
   * - Rich console output
     - ``geoips.features.rich_console_output``
     - ``GEOIPS_RICH_CONSOLE_OUTPUT``
     - ``false``
   * - Logging level
     - ``geoips.logging.level``
     - ``GEOIPS_LOGGING_LEVEL``
     - ``interactive``
   * - Logging format
     - ``geoips.logging.fmt_string``
     - ``GEOIPS_LOGGING_FMT_STRING``
     - ``%(asctime)s ...``
   * - Logging date format
     - ``geoips.logging.datefmt_string``
     - ``GEOIPS_LOGGING_DATEFMT_STRING``
     - ``%d_%H%M%S``
   * - Warning level
     - ``geoips.warning_level``
     - ``GEOIPS_WARNING_LEVEL``
     - ``default``
   * - Image threshold
     - ``geoips.test.output_checker_threshold_image``
     - ``GEOIPS_TEST_OUTPUT_CHECKER_THRESHOLD_IMAGE``
     - ``0.05``
   * - Print text checker output
     - ``geoips.test.print_text_output_checker_to_console``
     - ``GEOIPS_TEST_PRINT_TEXT_OUTPUT_CHECKER_TO_CONSOLE``
     - ``true``
   * - Prompt on mismatch
     - ``geoips.test.prompt_to_overwrite_comparison_file_if_mismatch``
     - ``GEOIPS_TEST_PROMPT_TO_OVERWRITE_COMPARISON_FILE_IF_MISMATCH``
     - ``false``
   * - Version
     - ``geoips.version``
     - ``GEOIPS_VERSION``
     - ``0.0.0``
   * - Documentation URL
     - ``geoips.docs_url``
     - ``GEOIPS_DOCS_URL``
     - GeoIPS docs URL
   * - Copyright
     - ``geoips.copyright``
     - ``GEOIPS_COPYRIGHT``
     - ``NRL-Monterey``
   * - Abbreviated copyright
     - ``geoips.copyright_abbreviated``
     - ``GEOIPS_COPYRIGHT_ABBREVIATED``
     - ``NRLMRY``
   * - Hostname
     - ``geoips.boxname``
     - ``BOXNAME``
     - auto (hostname)

Output path settings
--------------------

The following settings define sub-paths under ``geoips.outdirs``. Each
defaults to a relative path that is resolved against the output directory
at startup. You can override any of them with an absolute path.

.. list-table:: Output Path Settings
   :header-rows: 1
   :widths: 30 35 20

   * - Setting
     - YAML Path
     - Env Variable
   * - Presectored data
     - ``geoips.output_paths.presectored_data``
     - ``PRESECTORED_DATA_PATH``
   * - Preread data
     - ``geoips.output_paths.preread_data``
     - ``PREREAD_DATA_PATH``
   * - Preregistered data
     - ``geoips.output_paths.preregistered_data``
     - ``PREREGISTERED_DATA_PATH``
   * - Precalculated data
     - ``geoips.output_paths.precalculated_data``
     - ``PRECALCULATED_DATA_PATH``
   * - Clean imagery
     - ``geoips.output_paths.clean_imagery``
     - ``CLEAN_IMAGERY_PATH``
   * - Annotated imagery
     - ``geoips.output_paths.annotated_imagery``
     - ``ANNOTATED_IMAGERY_PATH``
   * - GeoTIFF imagery
     - ``geoips.output_paths.geotiff_imagery``
     - ``GEOTIFF_IMAGERY_PATH``
   * - Final data
     - ``geoips.output_paths.final_data``
     - ``FINAL_DATA_PATH``
   * - Pregenerated geolocation
     - ``geoips.output_paths.pregenerated_geolocation``
     - ``PREGENERATED_GEOLOCATION_PATH``
   * - Scratch
     - ``geoips.output_paths.scratch``
     - ``SCRATCH``
   * - Local scratch
     - ``geoips.output_paths.localscratch``
     - ``LOCALSCRATCH``
   * - Shared scratch
     - ``geoips.output_paths.sharedscratch``
     - ``SHAREDSCRATCH``
   * - Log directory
     - ``geoips.output_paths.logdir``
     - ``LOGDIR``
   * - GeoIPS data
     - ``geoips.output_paths.geoipsdata``
     - ``GEOIPSDATA``
   * - Ancillary data autogen
     - ``geoips.output_paths.ancildat_autogen``
     - ``GEOIPS_ANCILDAT_AUTOGEN``
   * - Ancillary data
     - ``geoips.output_paths.ancildat``
     - ``GEOIPS_ANCILDAT``
   * - TC WWW
     - ``geoips.output_paths.tcwww``
     - ``TCWWW``
   * - TC Private WWW
     - ``geoips.output_paths.tcprivatewww``
     - ``TCPRIVATEWWW``
   * - Public WWW
     - ``geoips.output_paths.publicwww``
     - ``PUBLICWWW``
   * - Private WWW
     - ``geoips.output_paths.privatewww``
     - ``PRIVATEWWW``
   * - TC decks DB
     - ``geoips.output_paths.tc_decks_db``
     - ``GEOIPS_TC_DECKS_DB``
   * - TC decks directory
     - ``geoips.output_paths.tc_decks_dir``
     - ``GEOIPS_TC_DECKS_DIR``
   * - TC decks type
     - ``geoips.tc_decks_type``
     - ``GEOIPS_TC_DECKS_TYPE``
   * - TC template
     - ``geoips.tc_template``
     - ``TC_TEMPLATE``

Configuration from plugin packages
==================================

External plugin packages can register their own configuration settings with
GeoIPS. Once a plugin is installed, its settings participate in the same
layered system (defaults → ``.geoips.yaml`` → environment variables), are
accessible in Python, and are included by ``geoips config create``.

Registering settings
--------------------

A plugin package defines a pydantic model for its settings and exposes a
:class:`~geoips.config.plugins.ConfigPlugin` object:

.. code-block:: python

    # my_pkg/config.py
    from pydantic import BaseModel, Field
    from geoips.config import ConfigPlugin


    class MyPkgSettings(BaseModel):
        max_workers: int = Field(4, description="Max parallel workers.")
        tile_cache: str | None = None


    CONFIG_PLUGIN = ConfigPlugin(name="my_pkg", settings_model=MyPkgSettings)

It then advertises this object through the ``geoips.config_plugins``
entry-point group in its ``pyproject.toml``:

.. code-block:: toml

    [project.entry-points."geoips.config_plugins"]
    my_pkg = "my_pkg.config:CONFIG_PLUGIN"

The entry-point name (``my_pkg``) must match ``ConfigPlugin.name``.

.. note::

   Plugin settings models should provide a default (or be ``Optional``) for
   every field. Settings are validated lazily on first access, so a plugin
   with an unset required field only raises when that plugin is accessed —
   but providing defaults avoids surprising failures entirely.

Accessing plugin settings
-------------------------

Plugin settings live under the ``plugins`` namespace, keyed by plugin name:

.. code-block:: python

    from geoips.config import config

    print(config.plugins.my_pkg.max_workers)
    print(config.plugins["my_pkg"].tile_cache)

In ``.geoips.yaml`` they are set under ``geoips.plugins.<name>``:

.. code-block:: yaml

    geoips:
      plugins:
        my_pkg:
          max_workers: 8
          tile_cache: /fast/disk/tiles

Environment variables
---------------------

Each plugin field is overridable via an auto-generated environment variable of
the form ``GEOIPS_PLUGIN_<PKG>_<FIELD>`` (uppercased, with ``.`` in nested
field paths replaced by ``_``). For the example above:

.. code-block:: bash

    export GEOIPS_PLUGIN_MY_PKG_MAX_WORKERS=16

Environment variables take precedence over the YAML file, which takes
precedence over the model defaults — identical to core settings. Auto-generated
names cannot collide with core GeoIPS variables; if a plugin declares explicit
``env_overrides`` aliases, GeoIPS raises a ``ConfigError`` on any collision.

Generation and validation
-------------------------

``geoips config create --all`` includes each installed plugin's settings under
``geoips.plugins.<name>``, with a per-plugin header comment and per-field
``# default: ...`` comments. ``geoips config validate`` validates each plugin
section against its registered model and warns about unknown plugins or
settings.

Environment Variable Overrides
==============================

While the ``.geoips.yaml`` file is the recommended way to configure GeoIPS,
environment variables remain fully supported and take the highest priority.
Setting an environment variable will override any corresponding YAML value or
default.

Core environment variables
--------------------------

The following environment variables cover the most commonly customized paths:

GEOIPS_OUTDIRS
^^^^^^^^^^^^^^

``GEOIPS_OUTDIRS`` specifies the base directory where GeoIPS will write
output files. This includes processed imagery, data products, and any
other output generated by GeoIPS processing workflows. The directory
structure within ``GEOIPS_OUTDIRS`` is typically organized by product
type, date, and sensor.

If not set, this variable defaults to ``$HOME/GEOIPS_OUTDIRS``.

.. code-block:: bash

    export GEOIPS_OUTDIRS=$HOME/geoips_outdirs

GEOIPS_PACKAGES_DIR
^^^^^^^^^^^^^^^^^^^

``GEOIPS_PACKAGES_DIR`` specifies the directory that contains GeoIPS
plugin packages. This is the parent directory where all GeoIPS-related
packages are installed, including the core GeoIPS package and any
additional plugin packages.

If you have multiple plugin packages (e.g., ``geoips``, ``data_fusion``,
``recenter_tc``) and you would like to make use of our testing scripts,
they should all be subdirectories of the path specified by
``GEOIPS_PACKAGES_DIR``.

.. code-block:: bash

    export GEOIPS_PACKAGES_DIR=$HOME/geoips_packages

GEOIPS_TESTDATA_DIR
^^^^^^^^^^^^^^^^^^^

``GEOIPS_TESTDATA_DIR`` specifies the directory where GeoIPS test data
is stored. This directory contains data used for testing and validating
GeoIPS functionality. The test data is typically organized by sensor
type and data format.

This variable must be set when running GeoIPS tests and producing example
or tutorial imagery.

.. code-block:: bash

    export GEOIPS_TESTDATA_DIR=$HOME/geoips_testdata

Setting up environment variables
--------------------------------

Below are examples of how to set these GeoIPS environment variables for
different shells and environments.

**Bash:**

.. code-block:: bash

    # Edit your ~/.bashrc
    vim ~/.bashrc
    # Add the following lines to your .bashrc
    export GEOIPS_TESTDATA_DIR=$HOME/geoips_testdata
    export GEOIPS_PACKAGES_DIR=$HOME/geoips_packages
    export GEOIPS_OUTDIRS=$HOME/geoips_outdirs
    # Reload your configuration
    source ~/.bashrc

**Zsh:**

.. code-block:: zsh

    # Edit your ~/.zshrc
    vim ~/.zshrc
    # Add the following lines to your .zshrc
    export GEOIPS_TESTDATA_DIR=$HOME/geoips_testdata
    export GEOIPS_PACKAGES_DIR=$HOME/geoips_packages
    export GEOIPS_OUTDIRS=$HOME/geoips_outdirs
    # Reload your configuration
    source ~/.zshrc

**Fish:**

.. code-block:: fish

    # Edit your ~/.config/fish/config.fish
    vim ~/.config/fish/config.fish
    # Add the following lines to your config.fish
    set -x GEOIPS_TESTDATA_DIR $HOME/geoips_testdata
    set -x GEOIPS_PACKAGES_DIR $HOME/geoips_packages
    set -x GEOIPS_OUTDIRS $HOME/geoips_outdirs
    # Reload your configuration
    source ~/.config/fish/config.fish

**Nix:**

.. code-block:: nix

    # In your home.nix, configuration.nix or in a flake:
    home.sessionVariables = {
      GEOIPS_TESTDATA_DIR = "${config.home.homeDirectory}/geoips_testdata";
      GEOIPS_PACKAGES_DIR = "${config.home.homeDirectory}/geoips_packages";
      GEOIPS_OUTDIRS = "${config.home.homeDirectory}/geoips_outdirs";
    };

**Conda:**

For Conda environments, it's recommended to use conda config vars to set
environment variables when you activate your environment. This means the
variables are only set when the GeoIPS environment is active.

.. code-block:: bash

    # Set PACKAGES_DIR first
    conda env config vars set GEOIPS_PACKAGES_DIR=$HOME/geoips

    # Reactivate environment for variables to take effect
    conda deactivate && conda activate geoips
    conda env config vars set GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/test_data
    conda env config vars set GEOIPS_OUTDIRS=$GEOIPS_PACKAGES_DIR/outdirs
    conda deactivate && conda activate geoips

System-Wide Environment Variables
=================================

GeoIPS recognizes a subset of system-wide environment variables.

NO_COLOR
--------

``NO_COLOR`` disables any colored output from your operating terminal.
Many software packages, including GeoIPS, may have commands that color
certain portions of their terminal output. Some users may not prefer
this, and in that case, you can set this variable to ``True`` in your
``.bashrc`` or comparable settings file.

.. note::

   Environment variable ``NO_COLOR`` will disable any colored output
   from the terminal, even if it's not produced via GeoIPS. For
   example, if this is set to ``True`` in your shell configuration,
   even pytest output will be monochrome. We chose this variable name
   as it is consistent with the settings that other software packages
   use.

Enabling this to ``True`` will prevent the GeoIPS command-line interface
(CLI) from coloring any of its terminal output.

By default, if not set in your shell configuration, GeoIPS will not
color any of its terminal output.

To set this environment variable, there are two options:

Temporary
^^^^^^^^^

Running the appropriate command below will disable colored terminal
output for a single session.

**Bash/Zsh:**

.. code-block:: bash

    export NO_COLOR='True'

**Fish:**

.. code-block:: fish

    set -x NO_COLOR 'True'

**Nix:**

.. code-block:: nix

    # In a nix-shell or shell.nix
    shellHook = ''
      export NO_COLOR='True'
    '';

**Conda:**

.. code-block:: bash

    # With your conda environment activated
    export NO_COLOR='True'

Persistent
^^^^^^^^^^

Add ``NO_COLOR`` to your ``.geoips.yaml`` file or use the environment
variable as described above to make the setting persistent.

To persist via configuration file:

.. code-block:: yaml

    geoips:
      features:
        no_color: true
