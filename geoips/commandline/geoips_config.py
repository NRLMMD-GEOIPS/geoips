# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "config" command.

Various configuration-based commands for setting up your geoips environment.
"""

import os
import pathlib
from os import listdir, remove
from os.path import join
import subprocess

import requests
import tempfile
import yaml
from pydantic import ValidationError

from numpy import any
from pluginify.commandline_typer import configure_logging
from pluginify.plugin_registry import PluginRegistry
import tarfile
from tqdm import tqdm

import geoips
from geoips.commandline.ancillary_info.test_data import test_dataset_dict
from geoips.commandline.geoips_command import GeoipsCommand, GeoipsExecutableCommand


def _collect_env_overrides() -> dict[str, str]:
    """Collect GeoIPS configuration values from environment variables.

    Iterates ``GEOIPS_ENV_MAP`` and returns a mapping of dot-path field
    names to values for every environment variable that is set.

    Returns
    -------
    dict[str, str]
        Mapping of ``"field.path"`` to raw string environment values.
    """
    from geoips.config.schema import GEOIPS_ENV_MAP

    overrides: dict[str, str] = {}
    for env_var in GEOIPS_ENV_MAP:
        raw = os.environ.get(env_var)
        if raw is not None:
            overrides[env_var] = raw
    return overrides


def _prompt_for_missing(
    overrides: dict[str, str], keys_to_prompt: list[str]
) -> dict[str, str]:
    """Interactively prompt the user for missing configuration values.

    Parameters
    ----------
    overrides : dict[str, str]
        Existing overrides keyed by environment variable name.
    keys_to_prompt : list[str]
        Environment variable names to prompt for if absent from *overrides*.

    Returns
    -------
    dict[str, str]
        New overrides from user input, keyed by environment variable name.
    """
    prompted: dict[str, str] = {}
    defaults = {
        "GEOIPS_OUTDIRS": os.path.join(
            os.environ.get("HOME", os.path.expanduser("~")), "geoips_outdirs"
        ),
        "GEOIPS_TESTDATA_DIR": os.path.join(
            os.environ.get("HOME", os.path.expanduser("~")), "geoips_testdata"
        ),
        "GEOIPS_PACKAGES_DIR": os.path.join(
            os.environ.get("HOME", os.path.expanduser("~")), "geoips_packages"
        ),
    }

    for key in keys_to_prompt:
        env_val = os.environ.get(key)
        if env_val is not None:
            continue

        default = defaults.get(key, "")
        value = input(f"\n  {key} [default: {default}]: ").strip()
        prompted[key] = value if value else default

    return prompted


def _build_nested_config(overrides: dict[str, str]) -> dict:
    """Convert flat env-var overrides into a nested YAML-ready dictionary.

    Uses ``GEOIPS_ENV_MAP`` to translate environment variable names into
    dot-separated field paths, then nests them.

    Parameters
    ----------
    overrides : dict[str, str]
        Mapping of environment variable names to raw string values.

    Returns
    -------
    dict
        Nested dictionary suitable for ``yaml.dump``.
    """
    from geoips.config.schema import GEOIPS_ENV_MAP
    from geoips.config.config import _cast_env_value

    result: dict = {}
    for env_var, raw_value in overrides.items():
        field_path = GEOIPS_ENV_MAP.get(env_var, "")
        if not field_path:
            continue
        cast = _cast_env_value(raw_value, field_path)
        parts = field_path.split(".")
        node = result
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = cast
    return result


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge *override* into *base* in-place.

    Nested dictionaries are merged; scalar values are replaced.

    Parameters
    ----------
    base : dict
        Target dictionary updated in-place.
    override : dict
        Source dictionary whose values take precedence.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _resolve_config_path(file_arg: pathlib.Path | None) -> pathlib.Path | None:
    """Resolve the config file path from an optional argument.

    If *file_arg* is provided, returns it. Otherwise searches standard
    locations via ``geoips.config.yaml_loader.find_project_config``.

    Parameters
    ----------
    file_arg : pathlib.Path or None
        User-supplied file path, or ``None`` to auto-search.

    Returns
    -------
    pathlib.Path or None
        Resolved path, or ``None`` if no config file was found.
    """
    if file_arg is not None:
        return file_arg

    from geoips.config.yaml_loader import find_project_config

    found = find_project_config()
    return pathlib.Path(found) if found else None


def _validate_config_file(file_path: pathlib.Path) -> list[str]:
    """Validate a GeoIPS YAML configuration file.

    Checks YAML syntax and validates all settings against the GeoIPS
    configuration model.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to the ``.geoips.yaml`` file to validate.

    Returns
    -------
    list[str]
        Human-readable error messages. An empty list means the file
        is valid.
    """
    from geoips.config.schema import GeoSettings

    errors: list[str] = []

    try:
        with open(file_path, "r") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        return [f"YAML syntax error: {exc}"]
    except OSError as exc:
        return [f"Cannot read file: {exc}"]

    if not isinstance(data, dict):
        return ["File must contain a YAML mapping (dictionary)."]

    geoips_data = data.get("geoips")
    if geoips_data is None:
        return ["Missing top-level 'geoips' key."]

    if not isinstance(geoips_data, dict):
        return ["The 'geoips' key must contain a mapping (dictionary)."]

    try:
        GeoSettings.model_validate(geoips_data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"])
            msg = err["msg"]
            errors.append(f"geoips.{loc}: {msg}")

    return errors


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
        # This is needed to ensure that we capture the logs from pluginify
        configure_logging()
        plugin_registry = PluginRegistry(namespace)
        plugin_registry.create_registries(packages, save_type)


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
        # This is needed to ensure that we capture the logs from pluginify
        configure_logging()
        plugin_registry = PluginRegistry(namespace)
        plugin_registry.delete_registries(packages)


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
                geoips.filenames.base_paths.PATHS["GEOIPS_PACKAGES_DIR"],
                "geoips",
                "setup",
                "check_system_requirements.sh",
            ),
            "test_data_github",
            test_dataset_name,
        ]
        retval = subprocess.call(call_list)
        if retval != 0:
            raise IOError(f"FAILED Did not successfully install '{test_dataset_name}'")


class GeoipsConfigCreate(GeoipsExecutableCommand):
    """Generate a .geoips.yaml config file from environment variables.

    Scans ``GEOIPS_*`` and unprefixed environment variables and writes
    them as a structured YAML configuration file. Interactively prompts
    for key variables (GEOIPS_OUTDIRS, GEOIPS_TESTDATA_DIR,
    GEOIPS_PACKAGES_DIR) that are not set in the environment.
    """

    name = "create"
    command_classes = []

    _KEYS_TO_PROMPT: list[str] = [
        "GEOIPS_OUTDIRS",
        "GEOIPS_TESTDATA_DIR",
        "GEOIPS_PACKAGES_DIR",
    ]

    def add_arguments(self):
        """Add arguments to the config-subparser for the create command."""
        self.parser.add_argument(
            "-o",
            "--output",
            type=pathlib.Path,
            default=pathlib.Path(".geoips.yaml"),
            help="Output path for the generated config file.",
        )
        self.parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            default=False,
            help="Overwrite the output file if it already exists.",
        )
        self.parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            default=False,
            help="Include all default settings, not just env overrides.",
        )
        self.parser.add_argument(
            "--no-prompt",
            action="store_true",
            default=False,
            help="Skip interactive prompts; generate only from environment variables.",
        )

    def __call__(self, args):
        """Run ``geoips config create``.

        Parameters
        ----------
        args : Namespace
            Parsed command-line arguments.
        """
        overrides = _collect_env_overrides()

        if not args.no_prompt:
            prompted = _prompt_for_missing(overrides, self._KEYS_TO_PROMPT)
            overrides.update(prompted)

        if not overrides and not args.all:
            print(
                "No GEOIPS environment variables found. "
                "Use --all to generate a complete config file with defaults, "
                "or remove --no-prompt for interactive setup."
            )
            return

        nested = _build_nested_config(overrides)

        if args.all:
            from geoips.config.schema import GeoSettings

            defaults = GeoSettings(
                outdirs=os.environ.get("GEOIPS_OUTDIRS", "")
            ).model_dump()
            _deep_merge(defaults, nested)
            nested = {"geoips": defaults}
        else:
            nested = {"geoips": nested}

        output_path = args.output.resolve()
        if output_path.exists() and not args.force:
            self.parser.error(
                f"File '{output_path}' already exists. Use --force to overwrite."
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as fh:
            yaml.dump(nested, fh, default_flow_style=False, sort_keys=False)

        num_env = len([k for k in overrides if os.environ.get(k)])
        num_prompted = len(overrides) - num_env

        parts = []
        if num_env:
            parts.append(f"{num_env} environment variable{'s' if num_env != 1 else ''}")
        if num_prompted:
            parts.append(
                f"{num_prompted} prompted value{'s' if num_prompted != 1 else ''}"
            )
        source = " and ".join(parts) if parts else "default settings"

        print(f"Generated {output_path} from {source}.")


class GeoipsConfigValidate(GeoipsExecutableCommand):
    """Validate a GeoIPS .geoips.yaml configuration file.

    Checks YAML syntax, verifies the structure against the GeoIPS
    configuration schema, and reports all errors found.
    """

    name = "validate"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the config-subparser for the validate command."""
        self.parser.add_argument(
            "-f",
            "--file",
            type=pathlib.Path,
            default=None,
            help="Path to the config file to validate. If not given, "
            "searches standard locations.",
        )
        self.parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            default=False,
            help="Only set the exit code; produce no output.",
        )

    def __call__(self, args):
        """Run ``geoips config validate``.

        Parameters
        ----------
        args : Namespace
            Parsed command-line arguments.
        """
        file_path = _resolve_config_path(args.file)

        if file_path is None:
            self.parser.error(
                "No config file found. Specify --file or place a .geoips.yaml "
                "in the current directory."
            )

        errors = _validate_config_file(file_path)

        if errors:
            if not args.quiet:
                print(f"Config file '{file_path}' is invalid:\n")
                for err in errors:
                    print(f"  {err}")
            self.parser.error("Validation failed.")
        else:
            if not args.quiet:
                print(f"Config file '{file_path}' is valid.")


class GeoipsConfig(GeoipsCommand):
    """Config top-level command for configuring your GeoIPS environment."""

    name = "config"
    command_classes = [
        GeoipsConfigCreate,
        GeoipsConfigCreateRegistries,
        GeoipsConfigDeleteRegistries,
        GeoipsConfigInstall,
        GeoipsConfigInstallGithub,
        GeoipsConfigValidate,
    ]
