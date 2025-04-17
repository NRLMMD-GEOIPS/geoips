# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

from numpy import any
from os import listdir, environ
from os.path import abspath, join
import requests
import tarfile

from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand


class GeoipsConfigInstall(GeoipsExecutableCommand):
    """Config Command Class for installing packages/data.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment.
    """

    name = "install"
    command_classes = []

    @property
    def geoips_testdata_dir(self):
        """String path to GEOIPS_TESTDATA_DIR."""
        if not hasattr(self, "_geoips_testdata_dir"):
            self._geoips_testdata_dir = environ["GEOIPS_TESTDATA_DIR"]
        return self._geoips_testdata_dir

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        self.parser.add_argument(
            "test_dataset_name",
            type=str.lower,
            choices=list(test_dataset_dict.keys()),
            help="GeoIPS Test Dataset to Install.",
        )
        self.parser.add_argument(
            "-o",
            "--outdir",
            type=str,
            default=self.geoips_testdata_dir,
            help="The full path to the directory you want to install this data to.",
        )

    def __call__(self, args):
        """Run the `geoips config install <test_dataset_name>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        test_dataset_name = args.test_dataset_name
        outdir = args.outdir
        test_dataset_url = test_dataset_dict[test_dataset_name]
        if any([test_dataset_name in fol for fol in listdir(outdir)]):
            print(
                f"Test dataset '{test_dataset_name}' already exists under "
                f"'{join(outdir, test_dataset_name)}*/'. See that "
                "location for the contents of the test dataset."
            )
        else:
            print(
                f"Installing {test_dataset_name} test dataset. This may take a while..."
            )
            self.download_extract_test_data(test_dataset_url, outdir)
            out_str = f"Test dataset '{test_dataset_name}' has been installed under "
            out_str += f"{outdir}/{test_dataset_name}/"
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
            self.parser.error(
                f"Error retrieving data from {url}; Status Code {resp.status_code}."
            )

    def extract_data_cautiously(self, response, download_dir):
        """Extract the GET Response cautiously and skip any dangerous members.

        Iterate through a Response and check that each member is not dangerous to
        extract to your machine. If it is, skip it.

        Where 'dangerous' is a filepath that is not part of 'download_dir'. File path
        maneuvering characters could be invoked ('../', ...), which we will not allow
        when downloading test data.

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
                    raise SystemExit("Found unsafe filepath in tar, exiting now.")
                tar.extract(m, path=download_dir)


class GeoipsConfig(GeoipsCommand):
    """Config top-level command for configuring your GeoIPS environment."""

    name = "config"
    command_classes = [GeoipsConfigInstall]
