# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "delete" command.

Currently only supports the deletion of plugin registry files.
"""

from pluginify.commandline_typer import configure_logging
from pluginify.plugin_registry import PluginRegistry

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand


class GeoipsDeleteRegistries(GeoipsExecutableCommand):
    """Command class for deleting plugin registries for plugin packages."""

    name = "registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the delete-subparser for the Delete Command."""
        pass

    def __call__(self, args):
        """Run the `geoips delete registries -n <namespace> -p <packages>` command.  # NOQA

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        packages = args.packages
        namespace = args.namespace
        # This is needed to ensure that we capture the logs from pluginify
        configure_logging()
        plugin_registry = PluginRegistry(namespace)
        plugin_registry.delete_registries(packages)


class GeoipsDelete(GeoipsCommand):
    """Delete top-level command for deleting configuration files for GeoIPS."""

    name = "delete"
    command_classes = [GeoipsDeleteRegistries]
