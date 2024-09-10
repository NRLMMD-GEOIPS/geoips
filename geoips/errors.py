# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS error module."""


class AsciiPaletteError(Exception):
    """Exception to be raised when encountering an invalid ascii palette text file."""

    pass


class EntryPointError(Exception):
    """Exception to be raised when an entry-point cannot be found."""

    pass


class PluginError(Exception):
    """Exception to be raised when there is an error in a GeoIPS plugin."""

    pass


class PluginRegistryError(Exception):
    """Exception to be raised when there is an error in a plugin registry."""

    pass


class PluginValidationError(Exception):
    """Exception to be raised when a plugin found in the registry is not valid."""

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
