# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "lint" command.

Runs the appropriate linters for one or more plugin packages based on the arguments
provided.
"""

from importlib import resources
import logging
import sys

from subprocess import call

from geoips.commandline.geoips_command import GeoipsExecutableCommand
from geoips.geoips_utils import is_editable

LOG = logging.getLogger(__name__)


class GeoipsLint(GeoipsExecutableCommand):
    """Command for running GeoIPS Linting Services."""

    name = "lint"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the lint-subparser for the lint Command."""
        self.parser.add_argument(
            "package_name",
            nargs="?",
            type=str,
            default="geoips",
            choices=self.plugin_package_names,
            help="GeoIPS Package to run linting tests on. Defaults to 'geoips'.",
        )

    def __call__(self, args):
        """Run all GeoIPS Linting Tests on the provided package."""
        package_name = args.package_name
        if not is_editable(package_name):
            # Package is installed in non-editable mode and we will not be able to
            # access unit tests. Raise a runtime error reporting this.
            print(
                f"Error: Package '{package_name}' is installed in non-editable mode and"
                " we are not able to access it's unit tests. For this command to "
                f"work, please install '{package_name}' in editable mode via: "
                f"'pip install -e <path_to_{package_name}>'",
                file=sys.stderr,
            )
            # We use a print to sys.stderr so monkeypatch unit tests can catch this
            # output
            raise RuntimeError(
                f"Package '{package_name}' isn't installed in editable mode."
            )
        lint_path = str(resources.files("geoips") / "../tests/utils/check_code.sh")
        package_path = str(resources.files(package_name) / "../.")
        for linter in ["bandit", "black", "flake8"]:
            call(["bash", lint_path, linter, package_path], shell=False)
