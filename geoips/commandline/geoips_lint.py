# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI command for linting a plugin package's source tree."""

from importlib import resources
import logging
from pathlib import Path

from subprocess import call

from geoips.commandline.geoips_command import GeoipsExecutableCommand
from geoips.geoips_utils import is_editable

LOG = logging.getLogger(__name__)


class GeoipsLint(GeoipsExecutableCommand):
    """Command for running GeoIPS linting checks."""

    name = "lint"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the lint command parser."""
        self.parser.add_argument(
            "--package-name",
            "-p",
            type=str,
            default="geoips",
            metavar="PACKAGE",
            choices=self.plugin_package_names,
            help=(
                "Installed GeoIPS plugin package to check. The package must be "
                "installed in editable mode. Defaults to 'geoips'."
            ),
        )

    def __call__(self, args):
        """Run all GeoIPS linting checks on the requested plugin package."""
        package_name = args.package_name
        if not is_editable(package_name):
            self.parser.exit(
                1,
                f"geoips lint: error: plugin package '{package_name}' is not "
                "installed in editable mode. Install it from its source directory "
                "with 'python -m pip install -e PATH'.\n",
            )

        geoips_package_path = Path(str(resources.files("geoips")))
        lint_path = geoips_package_path.parent / "tests" / "utils" / "check_code.sh"
        if not lint_path.is_file():
            self.parser.exit(
                1,
                "geoips lint: error: the GeoIPS lint runner was not found. Install "
                "GeoIPS in editable mode and retry.\n",
            )

        package_path = Path(str(resources.files(package_name))).parent
        failures = []
        for linter in ["bandit", "black", "flake8"]:
            try:
                return_code = call(
                    ["bash", str(lint_path), linter, str(package_path)], shell=False
                )
            except OSError as resp:
                self.parser.exit(
                    1,
                    f"geoips lint: error: unable to run {linter}: {resp}\n",
                )
            if return_code:
                failures.append(f"{linter} ({return_code})")

        if failures:
            self.parser.exit(
                1,
                "geoips lint: error: code-quality checks failed: "
                f"{', '.join(failures)}.\n",
            )
