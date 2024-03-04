"""Semi-Abstract CLI Test Class implementing attributes shared by sub-commands."""
import abc

from geoips.geoips_utils import get_entry_point_group

class BaseCliTest(abc.ABC):
    """Top-Level CLI Test Class which implements shared attributes for sub-commands."""

    _list_args = ["geoips", "list"]
    _list_interfaces_args = ["geoips", "list-interfaces"]
    _list_plugins_args = ["geoips", "list-plugins"]
    _list_packages_args = ["geoips", "list-packages"]
    _list_scripts_args = ["geoips", "list-scripts"]
    arg_list = [
        _list_args,
        _list_interfaces_args,
        _list_plugins_args,
        _list_packages_args,
        _list_scripts_args,
    ]

    def generate_id(self, args):
        """Generate an ID for the test-arguments provided."""
        return " ".join(args)

    @property
    def plugin_packages(self):
        """List of names of every installed GeoIPS package."""
        if not hasattr(self, "_plugin_packages"):
            self._plugin_packages = [
                ep.value for ep in get_entry_point_group("geoips.plugin_packages")
            ]
        return self._plugin_packages

    @abc.abstractproperty
    def all_possible_subcommand_combinations(self):
        """Every possible sub-command combination for each CLI command call.

        Ie. if we were testing 'geoips list', this property would be every possible
        combination of strings used to call 'geoips list'. This would take the form of:
            - [
                ["geoips", "list", "algorithms", "-p", "data_fusion"],
                ["geoips", "list", "algorithms", "-p", "geoips"],
                ["geoips", "list", "algorithms", "-p", "geoips_clavrx"],
                ...
                ["geoips", "list", <interface_name>, "-p", <pkg_name>],
                ["geoips", "list", <interface_name>],
                ["geoips", "list", <invalid_interface_name>]
                ["geoips", "list", <interface_name>, "-p", <invalid_pkg_name>],
                ...
            ]
        """
        pass