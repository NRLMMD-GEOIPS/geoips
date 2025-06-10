# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

from os import listdir, environ, remove
from os.path import abspath, join
import requests
import tempfile

from numpy import any
import tarfile
from tqdm import tqdm

from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand
from geoips.geoips_utils import get_remote_file_size
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

    @property
    def geoips_testdata_dir(self):
        """String path to GEOIPS_TESTDATA_DIR."""
        if not hasattr(self, "_geoips_testdata_dir"):
            self._geoips_testdata_dir = environ["GEOIPS_TESTDATA_DIR"]
        return self._geoips_testdata_dir

    def add_arguments(self):
        """Add arguments to the config-subparser for the Config Command."""
        self.parser.add_argument(
            "test_dataset_names",
            type=str.lower,
            nargs="+",
            choices=list(test_dataset_dict.keys()),
            help=(
                "Names of the GeoIPS test datasets to install. If 'all' is specified, "
                "GeoIPS will install all test datasets hosted on NextCloud. 'all' "
                "cannot be specified alongside other test dataset names."
            ),
        )
        self.parser.add_argument(
            "-o",
            "--outdir",
            type=str,
            default=self.geoips_testdata_dir,
            help="The full path to the directory you want to install this data to.",
        )
        self.parser.add_argument(
            "-f",
            "--force",
            default=False,
            action="store_true",
            help=(
                "Force the install to occur regardless of the file size potentially "
                "being downloaded."
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
        force_install = args.force

        if len(test_dataset_names) > 1 and "all" in test_dataset_names:
            self.parser.error(
                "Error: you cannot specify 'all' alongside other test dataset names. "
                "If 'all' is specified, that must be the only argument provided."
            )

        all_datasets = (
            True
            if len(test_dataset_names) == 1 and test_dataset_names[0] == "all"
            else False
        )

        install_dataset_names = (
            list(test_dataset_dict.keys()) if all_datasets else test_dataset_names
        )

        for test_dataset_name in install_dataset_names:
            test_dataset_url = test_dataset_dict[test_dataset_name]
            if (
                any([test_dataset_name in fol for fol in listdir(outdir)])
                and not force_install
            ):
                print(
                    f"Test dataset '{test_dataset_name}' already exists under "
                    f"'{join(outdir, test_dataset_name)}*/'. See that "
                    "location for the contents of the test dataset."
                )
            else:
                file_size = get_remote_file_size(test_dataset_url)
                do_install = "n"
                if not force_install:
                    do_install = input(
                        f"Remote compressed file size is {file_size} in size. The "
                        "uncompressed file size will likely be larger.\nAre you sure "
                        "you want to install it? [y/n]. "
                    )
                if do_install.lower() == "y" or force_install:
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
                else:
                    print(f"Skipping installation of {test_dataset_name}.")

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
        download_dir: str
            - The directory in which to download and extract the data into
        """
        with tarfile.open(filepath, mode="r:gz") as tar:
            members = tar.getmembers()

            # Validate and extract each member of the archive
            with tqdm(
                total=len(members), unit="file", desc="Extracting", ncols=80
            ) as progress:
                for m in tar:
                    if not abspath(join(download_dir, m.name)).startswith(download_dir):
                        raise SystemExit("Found unsafe filepath in tar, exiting now.")
                    tar.extract(m, path=download_dir)
                    progress.update(1)


class GeoipsConfig(GeoipsCommand):
    """Config top-level command for configuring your GeoIPS environment."""

    name = "config"
    command_classes = [
        GeoipsConfigInstall,
        GeoipsConfigCreateRegistries,
        GeoipsConfigDeleteRegistries,
    ]
