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


class PluginValidationError(PluginError):
    """Exception raised when a plugin fails schema/pydantic validation."""

    def __init__(self, plugin_name, interface_name, package, abspath, pydantic_exc):
        self.plugin_name = plugin_name
        self.interface_name = interface_name
        self.package = package
        self.abspath = abspath
        self.pydantic_exc = pydantic_exc
        super().__init__(self._build_message())

    def _build_message(self):
        summary = self._summarize_errors(self.pydantic_exc)
        return (
            f"Validation failed for {self.interface_name} plugin "
            f"'{self.plugin_name}' "
            f"(package: '{self.package}', file: '{self.abspath}').\n{summary}"
        )

    @staticmethod
    def _summarize_errors(exc):
        errors = exc.errors()
        field_errors = {}
        for err in errors:
            field = ".".join(
                str(loc) for loc in err["loc"] if not isinstance(loc, int)
            )
            if field not in field_errors:
                field_errors[field] = []
            field_errors[field].append(err["msg"])

        lines = [f"  {len(errors)} error(s) found. Summary by field:"]
        for field, msgs in field_errors.items():
            unique_msgs = list(dict.fromkeys(msgs))
            lines.append(f"    - {field}: {'; '.join(unique_msgs)}")
        return "\n".join(lines)
