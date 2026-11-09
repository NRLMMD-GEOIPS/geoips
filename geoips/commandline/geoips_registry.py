# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "create" command.

Creates configuration, registry, and sector image files.
"""

import logging

from pluginify.commandline_typer import configure_logging
from pluginify.plugin_registry import PluginRegistry

from geoips.commandline.geoips_command import (
    GeoipsCommand,
    GeoipsExecutableCommand,
)

LOG = logging.getLogger(__name__)


class GeoipsRegistryCreate(GeoipsExecutableCommand):
    """Command class for creating plugin registries for plugin packages."""

    name = "create"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the registry-subparser for the create Command."""
        self.parser.add_argument(
            "-s",
            "--save-type",
            default="json",
            type=str,
            choices=["json", "yaml"],
            help=(
                "The file format to save the registry as. Defaults to 'json', which is "
                "what's used by GeoIPS under the hood. For human readable output, you "
                "can provide the optional argument '-s yaml'."
            ),
        )

    def __call__(self, args):
        """Run the `geoips registry create -n <namespace> -s <save_type> -p <packages>` command.  # NOQA

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        packages = args.packages
        namespace = args.namespace
        save_type = args.save_type
        # This is needed to ensure that we capture the logs from pluginify
        configure_logging()
        plugin_registry = PluginRegistry(namespace)
        plugin_registry.create_registries(packages, save_type)


class GeoipsRegistryDelete(GeoipsExecutableCommand):
    """Command class for deleting plugin registries for plugin packages."""

    name = "delete"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the registry-subparser for the delete Command."""
        pass

    def __call__(self, args):
        """Run the `geoips registry delete -n <namespace> -p <packages>` command.  # NOQA

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


class GeoipsRegistry(GeoipsCommand):
    """Top-Level command for instantiating sub-command registry routines."""

    name = "registry"

    command_classes = [
        GeoipsRegistryCreate,
        GeoipsRegistryDelete,
    ]
