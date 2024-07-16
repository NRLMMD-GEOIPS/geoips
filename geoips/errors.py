# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS error module."""


class PluginError(Exception):
    """Exception to be raised when there is an error in a GeoIPS plugin."""

    pass


class PluginRegistryError(Exception):
    """Exception to be raised when there is an error in a plugin registry."""

    pass


class CoverageError(Exception):
    """Raise exception on data coverage error."""

    pass


class PluginPackageNotFoundError(Exception):
    """Raise exception stating a certain plugin package was not found."""

    pass


class CliError(Exception):
    """Raise exception on command line interface error."""

    pass
