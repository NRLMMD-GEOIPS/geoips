# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

import pathlib
from os import listdir, remove
from os.path import join
import subprocess
import requests
import tempfile

from numpy import any
import tarfile
from tqdm import tqdm

import geoips
from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.plugin_registry import PluginRegistry


class GeoipsConfigCreateRegistries(GeoipsExecutableCommand):
    """Config Command Class for creating plugin registries for plugin packages."""

    name = "create-registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
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
        """Run the `geoips config create-registries -n <namespace> -s <save_type> -p <packages>` command.  # NOQA

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        packages = args.packages
        namespace = args.namespace
        save_type = args.save_type
        plugin_registry = PluginRegistry(namespace)
        print(plugin_registry.create_registries(packages, save_type))


class GeoipsConfigDeleteRegistries(GeoipsExecutableCommand):
    """Config Command Class for deleting plugin registries for plugin packages."""

    name = "delete-registries"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        pass

    def __call__(self, args):
        """Run the `geoips config delete-registries -n <namespace> -p <packages>` command.  # NOQA

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        packages = args.packages
        namespace = args.namespace
        plugin_registry = PluginRegistry(namespace)
        print(plugin_registry.delete_registries(packages))


class GeoipsConfigInstall(GeoipsExecutableCommand):
    """Config Command Class for installing packages/data.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment.
    """

    name = "install"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        self.parser.add_argument(
            "test_dataset_names",
            type=str.lower,
            nargs="+",
            choices=list(test_dataset_dict.keys()) + ["all"],
            help=(
                "Names of the GeoIPS test datasets to install. If 'all' is specified, "
                "GeoIPS will install all test datasets hosted on NextCloud. 'all' "
                "cannot be specified alongside other test dataset names."
            ),
        )
        testdata_dir = geoips.filenames.base_paths.PATHS["GEOIPS_TESTDATA_DIR"]
        self.parser.add_argument(
            "-o",
            "--outdir",
            type=pathlib.Path,
            default=pathlib.Path(testdata_dir) if testdata_dir else pathlib.Path.cwd(),
            help=(
                "The full path to the directory you want to install this data to."
                "If not provided, this command will default to $GEOIPS_TESTDATA_DIR"
                "if set else will default to the current working directory."
            ),
        )

    def __call__(self, args):
        """Run the `geoips config install <test_dataset_names> -o <outdir>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        test_dataset_names = args.test_dataset_names
        outdir = args.outdir

        if not outdir.is_dir():
            self.parser.error(f"Specified output directory {outdir} doesn't exist.")
            raise FileNotFoundError(outdir)

        if len(test_dataset_names) > 1 and "all" in test_dataset_names:
            self.parser.error(
                "You cannot specify 'all' alongside other test dataset names. "
                "If 'all' is specified, that must be the only argument provided."
            )

        all_datasets = len(test_dataset_names) == 1 and test_dataset_names[0] == "all"

        install_dataset_names = (
            list(test_dataset_dict.keys()) if all_datasets else test_dataset_names
        )

        for test_dataset_name in install_dataset_names:
            test_dataset_url = test_dataset_dict[test_dataset_name]
            if any([test_dataset_name in fol for fol in listdir(outdir)]):
                print(
                    f"Test dataset '{test_dataset_name}' already exists under "
                    f"'{join(outdir, test_dataset_name)}*/'. See that "
                    "location for the contents of the test dataset."
                )
            else:
                print(
                    f"Installing {test_dataset_name} test dataset. This may take a "
                    "while..."
                )
                self.download_extract_test_data(test_dataset_url, outdir)
                out_str = (
                    f"Test dataset '{test_dataset_name}' has been installed under "
                    f"{outdir}/{test_dataset_name}/"
                )
                # Print the output of the command.
                print(out_str)

    def download_extract_test_data(self, url, download_dir):
        """Download the specified URL and write it to the corresponding download_dir.

        Will extract the data using tarfile and create an archive by bundling the
        associated files and directories together.

        Parameters
        ----------
        url: str
            - The url of the test dataset to download
        download_dir: pathlib.Path
            - The directory in which to download and extract the data into
        """
        resp = requests.get(url, stream=True, timeout=15)
        if resp.status_code == 200:

            total_size = int(resp.headers.get("Content-Length", 0))
            chunk_size = 1024 * 1024  # 1MB

            # Write the data to a temp file on disk. This is needed as files larger than
            # 1-2Gb might not fit in memory for some machines. Delete the temp file
            # after extraction has finished.
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                # Progress bar setup
                progress = tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc="Downloading",
                )

                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        tmp_file.write(chunk)
                        progress.update(len(chunk))

                progress.close()
                tmp_file.flush()

                # Seek back to the start of the file for extraction
                tmp_file.seek(0)

            print("Beginning data extraction...")
            self.extract_data_cautiously(tmp_file.name, download_dir)
            # Delete the temp file!
            remove(tmp_file.name)
        else:
            self.parser.error(
                f"Error retrieving data from {url}; Status Code {resp.status_code}."
            )

    def extract_data_cautiously(self, filepath, download_dir):
        """Extract the GET Response cautiously and skip any dangerous members.

        Iterate through a Response and check that each member is not dangerous to
        extract to your machine. If it is, skip it.

        Where 'dangerous' is a filepath that is not part of 'download_dir'. File path
        maneuvering characters could be invoked ('../', ...), which we will not allow
        when downloading test data.

        Parameters
        ----------
        filepath: str
            - The path to the temporary file to extract from.
        download_dir: pathlib.Path
            - The directory in which to download and extract the data into
        """
        with tarfile.open(filepath, mode="r:gz") as tar:
            members = tar.getmembers()

            # Validate and extract each member of the archive
            with tqdm(
                total=len(members), unit="file", desc="Extracting", ncols=80
            ) as progress:
                for m in tar:
                    member_path = (download_dir / m.name).resolve()
                    if not str(member_path).startswith(str(download_dir.resolve())):
                        raise SystemExit("Found unsafe filepath in tar, exiting now.")
                    tar.extract(m, path=download_dir, filter="tar")
                    progress.update(1)


class GeoipsConfigInstallGithub(GeoipsExecutableCommand):
    """Config Command Class for installing packages/data.

    Supports installation of packages and test data needed for testing and/or running
    your GeoIPS environment via github repositories.
    """

    name = "install-github"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        self.parser.add_argument(
            "test_dataset_name",
            type=str.lower,
            help="GeoIPS Test Dataset to Install from GitHub repository.",
        )

    def __call__(self, args):
        """Run the `geoips config install-github <test_dataset_name>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        test_dataset_name = args.test_dataset_name
        print(
            f"Running check_system_requirements.sh test_data_github {test_dataset_name}"
        )
        call_list = [
            "bash",
            join(
                geoips.filenames.base_paths.PATHS["GEOIPS_TESTDATA_DIR"],
                "geoips",
                "setup",
                "check_system_requirements.sh",
            ),
            "test_data_github",
            test_dataset_name,
        ]
        subprocess.call(call_list)


class GeoipsConfig(GeoipsCommand):
    """Config top-level command for configuring your GeoIPS environment."""

    name = "config"
    command_classes = [
        GeoipsConfigInstall,
        GeoipsConfigInstallGithub,
        GeoipsConfigCreateRegistries,
        GeoipsConfigDeleteRegistries,
    ]
