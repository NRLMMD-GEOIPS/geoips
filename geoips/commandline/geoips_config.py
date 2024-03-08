"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""
from importlib import resources
from os import environ
from subprocess import call

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand


class GeoipsConfigInstall(GeoipsExecutableCommand):
    """GeoipsConfigInstall Sub-Command for installing packages/data.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment.
    """
    subcommand_name = "install"
    subcommand_classes = []

    def add_arguments(self):
        self.subcommand_parser.add_argument(
            "test_dataset_name",
            type=str.lower,
            choices=list(self.test_dataset_dict.keys()),
            help="GeoIPS Test Dataset to Install."
        )

    def __call__(self, args):
        """Run the `geoips config install <test_dataset_name>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        test_dataset_name = args.test_dataset_name
        test_dataset_url = self.test_dataset_dict[test_dataset_name]
        script_dir = str(resources.files("geoips") / "../setup")
        GEOIPS_TESTDATA_DIR = str(environ["GEOIPS_TESTDATA_DIR"])
        command = f"python {script_dir}/download_test_data.py {test_dataset_url} "
        command += f"| tar -xz -C {GEOIPS_TESTDATA_DIR}"
        print(f"Installing {test_dataset_name} test data. This may take a while...")
        output = call(command, shell=True)
        out_str = f"Test Data {test_dataset_name} has been installed under "
        out_str += f"{GEOIPS_TESTDATA_DIR}/{test_dataset_name}/"
        print(out_str)
        return output


class GeoipsConfig(GeoipsCommand):
    """GeoipsConfig Sub-Command for configuring your GeoIPS environment."""
    subcommand_name = "config"
    subcommand_classes = [GeoipsConfigInstall]
