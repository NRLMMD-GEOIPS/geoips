
from importlib import resources
from subprocess import call

from geoips.commandline.cli_v2 import GeoipsCommand

class GeoipsRun(GeoipsCommand):
    """GeoipsRun Sub-Command for running process-workflows (procflows)."""
    subcommand_name = "run"

    def add_arguments(self):
        self.subcommand_parser.add_argument(
            "pkg_name",
            type=str.lower,
            default="geoips",
            choices=self.plugin_packages,
            help="GeoIPS Package to run a script from."
        )
        self.subcommand_parser.add_argument(
            "script_name",
            type=str,
            default="abi.static.Visible.imagery_annotated.sh",
            help="Script to run from previously selected package."
        )

    def run(self, args):
        """Run the provided GeoIPS command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        pkg_name = args.pkg_name
        script_name = args.script_name
        script_path = str(resources.files(pkg_name) / "../tests/scripts" / script_name)
        output = call(script_path, shell=True)
        return output