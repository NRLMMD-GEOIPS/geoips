# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS error module."""


class MissingRequiredXarrayMetadata(Exception):
    """Exception to be raised when required metadata missing from a geoips xarray.

    Can be used from reader plugins if required metadata is missing, or from the
    procflows to validate the xarray output of plugins.  At every stage, all GeoIPS
    xarrays should contain the required metadata.
    """

    pass


class NoValidFilesError(Exception):
    """Exception to be raised when there are no valid files found.

    Can be used from reader plugins if no valid files were passed to the reader.
    """

    pass


class OutputFormatterDatelineError(Exception):
    """Exception to be raised when there is a dateline error in an output formatter."""

    pass


class OutputFormatterInvalidProjectionError(Exception):
    """Exception to be raised when there is a projection error in an OutputFormatter."""

    pass


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
