# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS error module."""

from pluginify.errors import PluginError  # NOQA ; used in various imports

from yaml.constructor import ConstructorError


class GeoipsError(Exception):
    """Base class for all GeoIPS-specific exceptions.

    Catch this to handle any GeoIPS-originated error in a single except clause.
    """

    pass


class FileFormatError(ValueError, GeoipsError):
    """Exception to be raised when a file is badly formatted and cannot be used."""

    pass


class MissingRequiredXarrayMetadata(KeyError, GeoipsError):
    """Exception to be raised when required metadata missing from a geoips xarray.

    Can be used from reader plugins if required metadata is missing, or from the
    procflows to validate the xarray output of plugins.  At every stage, all GeoIPS
    xarrays should contain the required metadata.
    """

    pass


class NoValidFilesError(OSError, GeoipsError):
    """Exception to be raised when there are no valid files found.

    Can be used from reader plugins if no valid files were passed to the reader.
    """

    pass


class OutputFormatterDatelineError(ValueError, GeoipsError):
    """Exception to be raised when there is a dateline error in an output formatter."""

    pass


class OutputFormatterInvalidProjectionError(ValueError, GeoipsError):
    """Exception to be raised when there is a projection error in an OutputFormatter."""

    pass


class CoverageError(GeoipsError):
    """Raise exception on data coverage error."""

    pass


class PluginPackageNotFoundError(ModuleNotFoundError, GeoipsError):
    """Raise exception stating a certain plugin package was not found."""

    pass


class CliError(Exception):
    """Raise exception on command line interface error."""

    pass


class ConfigError(GeoipsError):
    """Raise exception on GeoIPS configuration error.

    Used for invalid configuration files, plugin config registration
    problems, and environment-variable collisions.
    """

    pass


class DuplicateKeyError(ConstructorError, GeoipsError):
    """Raised when a YAML mapping contains duplicate keys."""

    pass
