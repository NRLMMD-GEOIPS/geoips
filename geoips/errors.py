# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS error module."""

from pluginify.errors import PluginError  # NOQA ; used in various imports


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


# Preserve the historical GeoIPS import path while using the shared YAML
# utility package implementation.
from geoips_yaml_utils.errors import DuplicateKeyError


# ── DataTree / Workflow Domain Exceptions ─────────────────────────────────


class WorkflowSpecError(GeoipsError):
    """Workflow YAML fails pydantic validation.

    Raised when the YAML structure, field types, or required values do not
    conform to the workflow specification.
    """

    pass


class PluginResolutionError(GeoipsError):
    """A plugin ``name:`` reference in a step cannot be resolved.

    Raised when ``PluginRegistry.get_plugin(kind, name)`` returns no result
    for a given (kind, name) pair referenced in a workflow YAML.
    """

    pass


class DependencyCycleError(GeoipsError):
    """The ``depends_on`` graph contains a directed cycle.

    Raised during workflow validation when steps form a circular dependency
    chain that cannot be topologically sorted.
    """

    pass


class DataTreeSchemaError(GeoipsError):
    """Required attributes or child nodes are missing from a DataTree.

    Raised by the workflow runner when an output DataTree fails structural
    invariants (e.g., a step node missing required attrs).
    """

    pass


class RetentionConfigError(GeoipsError):
    """Conflicting or invalid retention settings.

    Raised when a workflow's retention policy combined with per-step ``keep``
    flags creates an unresolvable configuration.
    """

    pass


class BoundaryIOError(GeoipsError):
    """Reader or output_formatter I/O failure.

    Raised when a boundary step (reader or output_formatter) fails to read
    from or write to disk.
    """

    pass
