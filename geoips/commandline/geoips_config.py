"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

from importlib.resources import files
from os import listdir
from os.path import abspath, join
import requests
import tarfile

from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand


class GeoipsConfigInstall(GeoipsExecutableCommand):
    """GeoipsConfigInstall Sub-Command for installing packages/data.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment.
    """

    subcommand_name = "install"
    subcommand_classes = []

    @property
    def geoips_packages_dir(self):
        """String path to GEOIPS_PACKAGES_DIR."""
        if not hasattr(self, "_geoips_packages_dir"):
            self._geoips_packages_dir = "/".join(str(files("geoips")).split("/")[:-2])
        return self._geoips_packages_dir

    def add_arguments(self):
        """Add arguments to the list-subparser for the Config Command."""
        self.subcommand_parser.add_argument(
            "test_dataset_name",
            type=str.lower,
            choices=list(self.test_dataset_dict.keys()),
            help="GeoIPS Test Dataset to Install.",
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
        script_dir = self.geoips_packages_dir + "/geoips/setup"
        GEOIPS_TESTDATA_DIR = self.geoips_packages_dir + "/test_data"
        if test_dataset_name in listdir(GEOIPS_TESTDATA_DIR):
            out_str = f"Test dataset '{test_dataset_name}' already exists under "
            out_str += f"'{GEOIPS_TESTDATA_DIR}'. See that location for the contents "
            out_str += "of the test dataset."
            print(out_str)
        else:
            command = f"python {script_dir}/download_test_data.py {test_dataset_url} "
            command += f"| tar -xz -C {GEOIPS_TESTDATA_DIR}"
            print(
                f"Installing {test_dataset_name} test dataset. This may take a while..."
            )
            self.download_extract_test_data(test_dataset_url, GEOIPS_TESTDATA_DIR)
            out_str = f"Test dataset '{test_dataset_name}' has been installed under "
            out_str += f"{GEOIPS_TESTDATA_DIR}/{test_dataset_name}/"
            print(out_str)

    def download_extract_test_data(self, url, download_dir):
        """Download the specified URL and write it to the corresponding download_dir.

        Will extract the data using tarfile and create an archive by bundling the
        associated files and directories together.

        Parameters
        ----------
        url: str
            - The url of the test dataset to download
        download_dir: str
            - The directory in which to download and extract the data into
        """
        resp = requests.get(url, stream=True, timeout=15)
        if resp.status_code == 200:
            self.extract_data_cautiously(resp, download_dir)
        else:
            self.subcommand_parser.error(
                f"Error retrieving data from {url}; Status Code {resp.status_code}."
            )

    def extract_data_cautiously(self, response, download_dir):
        """Extract the GET Response cautiously and skip any dangerous members.

        Iterate through a Response and check that each member is not dangerous to
        extract to your machine. If it is, skip it.

        Parameters
        ----------
        response: Requests Response Object
            - The GET Response from retrieving the data url
        download_dir: str
            - The directory in which to download and extract the data into
        """
        with tarfile.open(fileobj=response.raw, mode="r|gz") as tar:
            # Validate and extract each member of the archive
            for m in tar:
                if not abspath(join(download_dir, m.name)).startswith(download_dir):
                    raise SystemExit(
                        "Found unsafe filepath in tar, exiting now."
                    )
                tar.extract(m, path=download_dir)


class GeoipsConfig(GeoipsCommand):
    """GeoipsConfig Sub-Command for configuring your GeoIPS environment."""

    subcommand_name = "config"
    subcommand_classes = [GeoipsConfigInstall]
