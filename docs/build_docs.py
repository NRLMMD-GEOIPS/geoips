# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Builds geoips and geoips plugin documentation."""

import tempfile
import importlib.resources
import importlib.util
import warnings
import logging
import logging.handlers
import argparse
import shutil
import os
from subprocess import call

import brassy.actions.build_release_notes as brassy_build
import brassy.utils.CLI  # noqa # because of a brassy bug; will be fixed in next vers
from rich.logging import RichHandler
from rich.traceback import install as install_rich_tracebacks
from rich.logging import Console
from rich.progress import Progress
import rich_argparse
import pygit2
import yaml
import sphinx.cmd.build as sphinx_build_module
from sphinx.ext.apidoc import main as sphinx_apidoc

from update_release_note_index import main as generate_release_note_index

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def init_logger(use_rich):
    """
    Initialize and configure the logger.

    Parameters
    ----------
    use_rich : bool
        If True, sets up rich logging else use standard stream logging

    Returns
    -------
    logger : logging.Logger
        The configured logger instance
    """
    if use_rich:
        install_rich_tracebacks()
        logging_handlers = [RichHandler(rich_tracebacks=True)]
    else:
        logging_handlers = [logging.StreamHandler()]

    logging.basicConfig(level=logging.DEBUG, datefmt="[%X]", handlers=logging_handlers)
    logger = logging.getLogger("build_docs")
    return logger


def parse_args_with_argparse():
    """
    Parse and validate command-line arguments provided to the script.

    Returns
    -------
    args : argparse.Namespace
        An object containing the parsed command-line arguments.
    """
    # Initialize parser with an example usage in the description
    parser = argparse.ArgumentParser(
        description=(
            "Build Sphinx documentation for GeoIPS related packages.\n"
            "Example: build_docs.py /path/to/repo geoips"
        ),
        formatter_class=rich_argparse.RichHelpFormatter,
    )

    # Required positional arguments
    parser.add_argument(
        "package_name",
        type=str,
        help="Name of the package to build (e.g., geoips, data_fusion).",
    )

    # Optional argument: path to documentation templates
    parser.add_argument(
        "--geoips-docs-path",
        type=str,
        default=None,
        help="Path to GeoIPS documentation templates.",
    )
    parser.add_argument(
        "--license-url",
        type=str,
        default=None,
        help=(
            "Path to GeoIPS license."
            "Default is https://github.com/NRLMMD-GEOIPS/[package_name]"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output dir to write built docs to",
    )
    parser.add_argument(
        "--save-temp-dir",
        type=str,
        default=None,
        help="Output dir to write temporary build files to (for debugging purposes)",
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        default=None,
        help="Path to the repository (e.g., /path/to/geoips)."
        "If not provided uses [package_name] to find the packages directory"
        "Must be an existing directory.",
    )

    parser.add_argument(
        "-f",
        "--force",
        default=False,
        action="store_true",
        help="Replace output dir if it already exists",
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.repo_path:
        try:
            package_path = os.path.dirname(
                str(importlib.resources.files(args.package_name))
            )
            if not package_path:
                raise ModuleNotFoundError
            pygit2.Repository(package_path)
            args.repo_path = package_path
        except ModuleNotFoundError as e:
            raise e(f"Could not automatically find repo_path for {args.package_name}.")
        except pygit2.GitError:
            raise pygit2.GitError(
                "Could not automatically find usable repo_path for "
                f"{args.package_name}. Found {package_path} but it is not a git repo"
            )

    if not args.output_dir:
        output_dir = os.getenv("GEOIPS_DOCSDIR", None)
        if output_dir:
            warnings.warn(
                f"Using output dir value {output_dir} from environmental variable "
                "$GEOIPS_DOCSDIR. This functionality is DEPRECATED and will be "
                "removed. Please pass $GEOIPS_DOCSDIR as --output-dir $GEOIPS_DOCSDIR "
                "for the same functionality."
            )
        else:
            output_dir = os.path.join(args.repo_path, "build", "sphinx", "html")
        args.output_dir = output_dir

    if args.package_name == "geoips":
        args.geoips_docs_path = os.path.join(args.repo_path, "docs")
    elif not args.geoips_docs_path:
        docs_path_env = (
            os.getenv("GEOIPS_PACKAGES_DIR", "") + "/geoips/docs"
            if os.getenv("GEOIPS_PACKAGES_DIR")
            else None
        )
        if docs_path_env:
            warnings.warn(
                "GeoIPS docs path set to $GEOIPS_PACKAGES_DIR/geoips/docs, but this "
                "fall back is deprecated. Please start passing with "
                "--geoips-docs-path $GEOIPS_PACKAGES_DIR"
            )
            args.geoips_docs_path = docs_path_env
        else:
            raise argparse.ArgumentError(
                "Please pass geoips docs path to " "build plugin documentation"
            )

    if not args.license_url:
        repo_url = os.getenv("GEOIPS_REPO_URL")
        if repo_url:
            warnings.warn(
                "Using the environmental variable $GEOIPS_REPO_URL as value for "
                "--license-url. This functionality is deprecated and will be removed. "
                "Please pass in using --license-url $GEOIPS_REPO_URL. Alternatively,"
                "you can unset $GEOIPS_REPO_URL and the URL will default to"
                "https://github.com/NRLMDD-GEOIPS/package_name"
            )
        else:
            repo_url = "https://github.com/NRLMMD-GEOIPS/" + args.package_name
        args.license_url = repo_url

    return args


def validate_path_exists_and_is_git_repo(repo_path, logger=logging.getLogger(__name__)):
    """
    Ensure given path exists and is a valid Git repository.

    Parameters
    ----------
    repo_path : str
        The file system path to validate.
    logger : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist.
    pygit2.GitError
        If the path is not a valid Git repository.
    """
    if not os.path.exists(repo_path):
        logger.critical(f"Path does not exist: {repo_path}")
        raise FileNotFoundError
    try:
        pygit2.Repository(repo_path)
    except pygit2.GitError as e:
        logger.critical(f"{repo_path} is not a valid git repo")
        raise e


def validate_package_is_installed(package_name, logger=logging.getLogger(__name__)):
    """
    Verify that the specified package is installed in the current Python environment.

    Parameters
    ----------
    package_name : str
        The name of the package to check for installation.
    logger : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.

    Raises
    ------
    ModuleNotFoundError
        If the package is not found in the current Python environment.
    """
    if importlib.util.find_spec(package_name) is None:
        logger.critical(f"ERROR: Package {package_name} is not installed")
        raise ModuleNotFoundError


def get_section_replace_string(section):
    """
    Create a placeholder string used in the index template for a given section.

    Parameters
    ----------
    section : str
        The name of the section.

    Returns
    -------
    str
        A placeholder string corresponding to the section.

    """
    return section.upper() + "_OPTIONAL"


def get_sections(package_name):
    """
    Return sections.

    Returns a list of required and optional sections.

    Returns
    -------
    required_sections : list of str
        List of required section names.
    optional_sections : list of str
        List of optional section names.

    Notes
    -----
    This could potentially be from a config file in the future. For now, it is hard
    coded like the original build_docs.sh script.
    """
    with open(os.path.join(__location__, "docs-sections.yaml"), "r") as f:
        section_data = yaml.safe_load(f)

    section_data["optional"] = section_data["current"] + section_data["legacy"]

    return (
        (x.replace("PKGNAME", package_name) for x in section_data[category])
        for category in ["required", "optional"]
    )


def return_file_content(template_path):
    """
    Render file into a string.

    This function reads the content of the template file
    and returns the resulting string.

    Parameters
    ----------
    template_path : str
        The file path to the template.

    Returns
    -------
    str
        The rendered template content as a string.
    """
    with open(template_path, "rt") as template_file:
        return template_file.read()


def update_content_for_section(
    build_dir, content, section, is_optional=False, log=logging.getLogger(__name__)
):
    """
    Replace placeholders in the content with actual section paths if they exist.

    This function checks if the section exists in the build directory. If it does,
    it replaces the placeholder with the section's index path. If the section is
    optional and does not exist, it removes the placeholder from the content.

    Parameters
    ----------
    build_dir : str
        The directory where the documentation is being built.
    content : str
        The content string containing placeholders to be updated.
    section : str
        The name of the section to process.
    is_optional : bool, optional
        Whether the section is optional; defaults to False.
    log : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.

    Returns
    -------
    str
        The content with placeholders replaced or removed.

    Raises
    ------
    FileNotFoundError:
        If non-optional section does not exist
    """
    section_path = os.path.join(build_dir, section, "index.rst")
    if not is_optional and not os.path.exists(section_path):
        if not (
            section == "releases" and os.path.exists(os.path.join(build_dir, section))
        ):  # need this second level check because releases/index.rst is auto-generated
            log.debug(f"Files in {os.path.join(build_dir, section)}")
            log.debug(os.listdir(os.path.join(build_dir, section)))
            raise FileNotFoundError(
                f"Required section {section} does not exist as {section_path}"
            )
    if is_optional and not os.path.exists(section_path):
        log.debug(f"Not adding optional section {section}")
        return content.replace(get_section_replace_string(section), "")
    if is_optional:
        log.debug(f"Including optional section {section}")
    return content.replace(get_section_replace_string(section), f"{section}/index")


def generate_top_level_index_file(
    build_dir,
    geoips_docs_dir,
    package_name,
    required_sections,
    optional_sections,
    log=logging.getLogger(__name__),
):
    """
    Create top-level index.rst file from template and available sections.

    This function reads the index template, replaces placeholders with section paths
    or removes them if they are optional and not present. It replaces the package name
    placeholder with the actual package name. The result is written to the index.rst
    file in the build directory.

    Parameters
    ----------
    build_dir : str
        Directory where the documentation is being built.
    geoips_docs_dir : str
        Path to the GeoIPS documentation dir.
    package_name : str
        The name of the package being documented.
    required_sections : list of str
        Sections that must be included in the index.
    optional_sections : list of str
        Sections that can be included if they exist.
    log : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.
    """
    template_index_file_path = os.path.join(
        geoips_docs_dir, "source", "_templates", "index.template.rst"
    )
    build_index_file_path = os.path.join(build_dir, "index.rst")

    content = return_file_content(template_index_file_path)

    # Replace required sections
    # for section in required_sections:
    #    content = update_content_for_section(build_dir, content, section, log=log)

    # Replace optional sections
    for section in optional_sections:
        content = update_content_for_section(
            build_dir, content, section, is_optional=True, log=log
        )

    # Replace package name
    content = content.replace("PKGNAME", package_name)

    with open(build_index_file_path, "wt") as build_index_file:
        build_index_file.write(content)


def copy_template_files_to_non_geoips_repo(geoips_docs_dir, build_dir):
    """
    Copy static and template files to the build directory for non-GeoIPS packages.

    This function copies necessary static files, LaTeX styles, and templates from the
    GeoIPS documentation directory to the build directory to ensure consistency in
    documentation appearance for packages other than GeoIPS.

    Parameters
    ----------
    geoips_docs_dir : str
        The path to the GeoIPS documentation templates directory.
    build_dir : str
        The directory where the documentation is being built.
    """
    shutil.copytree(
        os.path.join(geoips_docs_dir, "source", "_static"),
        os.path.join(build_dir, "_static"),
    )
    template_path = os.path.join(build_dir, "_templates")
    os.makedirs(template_path, exist_ok=True)
    shutil.copy(
        os.path.join(geoips_docs_dir, "source", "_templates", "geoips_footer.html"),
        template_path,
    )


def create_conf_py_from_template(build_dir, geoips_docs_dir, package_name):
    """
    Generate the Sphinx configuration file (conf.py) from GeoIPS template.

    This function reads the template conf.py file, replaces the package name placeholder
    with the actual package name, and writes the result to the conf.py file in the build
    directory. The custom conf.py is used by Sphinx during the build process.

    Parameters
    ----------
    build_dir : str
        The directory where the documentation is being built.
    geoips_docs_dir : str
        The path to the GeoIPS documentation docs directory.
    package_name : str
        The name of the package being documented.
    """
    template_conf_file_path = os.path.join(
        geoips_docs_dir, "source", "_templates", "sphinx_conf.template.py"
    )
    build_conf_file_path = os.path.join(build_dir, "conf.py")

    with open(template_conf_file_path, "rt") as template_conf_file:
        with open(build_conf_file_path, "wt") as build_conf_file:
            for line in template_conf_file:
                build_conf_file.write(line.replace("PKGNAME", package_name))


def stage_docs_files_for_building(
    source_dir,
    package_name,
    geoips_docs_dir,
    build_dir,
    log=logging.getLogger(__name__),
):
    """
    Set up the documentation source files in the build directory before building.

    This function copies the package documentation source files into a build directory.
    If the package isn't 'geoips', it setups up template files from the GeoIPS docs.
    It then creates a customized conf.py and index.rst files tailored for the package.

    Parameters
    ----------
    source_dir : str
        The source directory containing the package's documentation files.
    package_name : str
        The name of the package being documented.
    geoips_docs_dir : str
        The path to the GeoIPS documentation templates.
    build_dir : str
        The directory where the documentation will be built.
    log : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.
    """
    shutil.copytree(source_dir, build_dir)  # copy docs files over

    if not package_name == "geoips":
        copy_template_files_to_non_geoips_repo(geoips_docs_dir, build_dir)

    create_conf_py_from_template(build_dir, geoips_docs_dir, package_name)

    required_sections, optional_sections = get_sections(package_name)
    generate_top_level_index_file(
        build_dir,
        geoips_docs_dir,
        package_name,
        required_sections,
        optional_sections,
        log,
    )


def build_module_apidocs_with_sphinx(
    module_path, apidoc_build_path, log=logging.getLogger(__name__)
):
    """
    Generate API documentation RST files using Sphinx apidoc.

    This function constructs the necessary arguments for sphinx-apidoc to generate
    the API documentation RST files, excluding certain paths as specified. It then
    executes sphinx-apidoc and checks for successful completion. It calls the ``main``
    function of sphinx, and passes arguments to it. This is clunky, but after
    reviewing the sphinx codebase it seemed to be the best option. Further,
    there is no (or at least extremely little) documentation on how to use
    sphinx inside of python; hence the current approach.

    Parameters
    ----------
    module_path : str
        The path to the Python module dir for which to generate API docs.
    apidoc_build_path : str
        The output directory where the generated RST files will be placed.
    log : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.

    Raises
    ------
    Exception
        If the sphinx-apidoc command fails.
    """
    arguments = [
        "--no-toc",
        "-o",  # flag for output path
        apidoc_build_path,  # output path
        module_path,  # module path
        "*/lib/*",  # exclude path
    ]
    
    # See https://github.com/sphinx-doc/sphinx/issues/8664
    # and https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html
    # for more info on why they are set.
    # The enable overrideing child class docstrings to be rendered
    os.environ["SPHINX_APIDOC_OPTIONS"] = "members,show-inheritance"
    log.debug(f"Running sphinx apidoc with arguments '{' '.join(arguments)}'")

    if not sphinx_apidoc(arguments) == 0:
        raise Exception("Sphinx API Doc build failed")


def build_docs_with_sphinx(build_dir, built_dir, log=logging.getLogger(__name__)):
    """
    Build documentation HTML files using Sphinx.

    See also docstring for build_module_apidocs_with_sphinx for information
    on why command line-like arguments are being passed to sphinx like this.

    Parameters
    ----------
    build_dir : str
        The source directory containing the documentation to be built.
    built_dir : str
        The destination directory where the built HTML files will be placed.
    log : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.

    Notes
    -----
    This overrides the exception handler to re-raise exceptions, allowing for error
    handling inline.
    """
    arguments = [
        "-b",  # builder name
        "html",  # uses the html builder
        "-W",  # fail on warnings
        "-v",
        build_dir,  # folder to build from
        built_dir,  # folder to build to
    ]
    log.debug(f"Running sphinx build with arguments '{' '.join(arguments)}'")

    # for currying, prevents recursion error
    original_handler = sphinx_build_module.handle_exception

    def override_handle_exception(app, args, exc, error):
        original_handler(app, args, exc, error)
        raise exc  # raise exceptions so they bubble up in this script

    sphinx_build_module.handle_exception = override_handle_exception
    sphinx_build_module.main(arguments)  # build docs with sphinx


def build_release_note_from_dir_with_brassy(
    release_dir, release_filename, version, header_file, log=logging.getLogger(__name__)
):
    """
    Build release note file by combining YAML files in a specified directory.

    This function aggregates YAML files in the given `release_dir` directory
    and generates a release note in the specified `release_filename` file
    with the `brassy` build tool.

    Parameters
    ----------
    release_dir : str
        Path to the directory containing the YAML files to include in the
        release notes.
    release_filename : str
        Path to the output file where the generated release note will be saved.
    version : str
        Version string to label the release note content.
    header_file : str
        Path to a header file to include at the beginning of the release note.
    log : logging.Logger, optional
        Logger for debug information (default is a logger named after the
        module).

    Returns
    -------
    None
        This function does not return a value; it writes the release note to
        `release_filename`.

    Examples
    --------
    >>> build_release_note_from_dir_with_brassy(
    ...     release_dir="/path/to/yaml_files",
    ...     release_filename="release_notes.rst",
    ...     version="1.2.3",
    ...     header_file="header.rst"
    ... )
    This example writes the release notes from YAML files in `/path/to/yaml_files`
    to `release_notes.yaml`, as version "1.2.3" and includes the content
    of `header.md` as a header.
    """
    log.debug(
        f"Building yaml files in {release_dir} into {release_filename} using brassy"
    )
    with open(release_filename, "w") as f:
        release_note_content = brassy_build.build_release_notes(
            [release_dir],
            Console(),
            Progress().open,
            version=version,
            header_file=header_file,
        )
        f.write(release_note_content)


def build_release_notes_with_brassy(
    releases_dir,
    license_url,
    log=logging.getLogger(__name__),
    save_temp_dir=None,
):
    """Generate release notes for each subdirectory in a specified releases directory.

    Uses the `brassy` build tool and the `pinkrst` formatting tool to build release
    notes with a license disclaimer at the top.

    Parameters
    ----------
    releases_dir : str
        The path to the main directory containing individual release directories.
    license_url : str
        The URL pointing to the license or distribution statement for the release notes.
    log : logging.Logger, optional
        Logger instance used for logging debug and warning messages. By default,
        uses a logger with the module's name.
    save_temp_dir : str
        Optional path to directory to save temp files for reference in debugging

    Notes
    -----
    Each subdirectory in `releases_dir` is assumed to correspond to a release version.
    This function generates a header file containing a distribution statement that
    includes `license_url`. For each release directory, an `.rst` file with the
    release notes is created and processed by `build_release_note_from_dir_with_brassy`.
    The function will ignore directories named "upcoming" and log a warning.

    Warnings
    --------
    Directories in `releases_dir` named "upcoming" are skipped, and a warning logged.

    Raises
    ------
    FileNotFoundError
        If `releases_dir` does not exist or is not a directory.
    PermissionError
        If there are permissions issues accessing `releases_dir` or its subdirectories.

    Example
    -------
    >>> build_release_notes_with_brassy('/path/to/releases',
    >>>                                 'https://example.com/license')

    """
    release_dirs = filter(
        os.path.isdir,
        [os.path.join(releases_dir, rd) for rd in os.listdir(releases_dir)],
    )

    with tempfile.NamedTemporaryFile(mode="w") as header_file:
        header_file.write(
            "\n".join(
                [
                    ".. dropdown:: Distribution Statement",
                    "  | This file is auto-generated. Please abide by the license",
                    f"  | found at {license_url}.",
                ]
            )
        )

        for release_dir in release_dirs:
            release_filename = release_dir + ".rst"
            release_version = release_dir.replace(releases_dir + "/", "")
            if release_version == "upcoming":
                log.warning(
                    f"Skipping release dir {release_dir}"
                    "because it's version is 'upcoming'"
                )
            log.debug(f"Setting version of {release_filename} to {release_version}")
            build_release_note_from_dir_with_brassy(
                release_dir, release_filename, release_version, header_file.name
            )
            if save_temp_dir:
                log.info(f"Writing temp files to {save_temp_dir}")
                os.makedirs(save_temp_dir, mode=0o755, exist_ok=True)
                shutil.copy(release_filename, save_temp_dir)
            # TODO: pythonize and call directly; requires update to pink
            call(["pink", release_filename], shell=False)

    log.info(
        "Generating index.rst for release notes, "
        "this will be done by brassy in the future."
    )
    generate_release_note_index(os.path.join(releases_dir, "index.rst"), releases_dir)


def get_auxiliary_files():
    """
    Load auxiliary file information from a YAML configuration file.

    This function reads the `auxiliary_files.yaml` file located in the directory
    specified by `__location__` and returns the parsed dictionary of auxiliary
    files. The returned data corresponds to the "auxiliary files" field in the
    YAML file, which should be defined relative to the repository's root directory.

    Returns
    -------
    dict
        A dictionary containing information about auxiliary files as defined
        under the "auxiliary files" key in the YAML file.

    Examples
    --------
    >>> aux_files = get_auxiliary_files()
    >>> aux_files
    {'config.json': 'config/config.json', 'notes.txt': 'docs/notes.txt'}

    Notes
    -----
    The `__location__` variable must point to the directory containing the
    `auxiliary_files.yaml` file.
    """
    with open(os.path.join(__location__, "auxiliary_files.yaml"), "r") as f:
        data = yaml.safe_load(f)
    return data["auxiliary files"]  # relative to root of repo_dir


def import_non_docs_files(repo_dir, build_dir, log=logging.getLogger(__name__)):
    """
    Copy auxiliary non-documentation files from the repository to the build directory.

    Creates an 'import' subdirectory within the specified build directory and
    copies auxiliary files from the repository directory to this 'import' directory.

    Parameters
    ----------
    repo_dir : str
        Path to the repository directory containing the source files.
    build_dir : str
        Path to the build directory where the files will be copied.

    Raises
    ------
    FileNotFoundError
        If any of the auxiliary files do not exist in the repository directory.

    Notes
    -----
    The list of auxiliary files to copy is defined within the function.
    """
    auxiliary_files = get_auxiliary_files()
    import_dir = os.path.join(build_dir, "import")
    os.mkdir(import_dir)
    for file in auxiliary_files:
        filename = os.path.basename(file)
        source = os.path.join(repo_dir, file)
        dest = os.path.join(import_dir, filename)
        log.info(f"Copying {source} to {dest}")
        try:
            log.info(f"Copying {source} to {dest}")
            shutil.copyfile(source, dest)
        except FileNotFoundError:
            log.warning(f"Could not fine aux file {source}")


def build_html_docs(
    repo_dir,
    build_dir,
    geoips_docs_dir,
    package_name,
    output_dir,
    force_overwrite,
    license_url,
    log=logging.getLogger(__name__),
    save_temp_dir=None,
):
    """
    Build the HTML documentation for package.

    Sets up the documentation files, generates API documentation,
    builds the HTML documentation using Sphinx, and then copies the built files
    to the specified output directory if the build is successful.

    Parameters
    ----------
    repo_dir : str
        The root directory of the package's repository.
    build_dir : str
        The directory where the documentation source files will be staged.
    geoips_docs_dir : str
        The path to the GeoIPS documentation templates (usually geoips/docs).
    package_name : str
        The name of the package that docs are being built for.
    output_dir : str
        The directory where the final built documentation will be placed.
    force_overwrite : bool
        If true, replace output_dir if exists already.
    license_url : str
        URL that points to the license for the package.
    log : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.
    save_temp_dir : str
        Optional path to directory to save temp files for reference in debugging
    """
    log.info("Setting docs files up for building")
    # copy and validate files
    stage_docs_files_for_building(
        os.path.join(repo_dir, "docs", "source"),
        package_name,
        geoips_docs_dir,
        build_dir,
        log=log,
    )

    # grab auxillary files not in docs and place them in "import" dir
    import_non_docs_files(repo_dir, build_dir, log=log)

    # build release rst files
    log.info("Building API docs")
    releases_dir = os.path.join(build_dir, "releases")
    build_release_notes_with_brassy(
        releases_dir, license_url, save_temp_dir=save_temp_dir
    )

    # build api doc rst files
    apidoc_build_path = os.path.join(build_dir, f"{package_name}_api")
    module_path = os.path.join(repo_dir, package_name)  # module path
    build_module_apidocs_with_sphinx(module_path, apidoc_build_path, log=log)

    # build final html files
    with tempfile.TemporaryDirectory() as built_dir:
        log.info("Building docs")
        build_docs_with_sphinx(build_dir, built_dir, log=log)
        log.debug("Docs built successfully")
        if os.path.exists(output_dir) and force_overwrite:
            log.info(
                f"Removing output directory {output_dir} in preparation of writing"
                "built docs"
            )
            shutil.rmtree(output_dir)
        try:
            shutil.copytree(built_dir, output_dir)
        except FileExistsError:
            raise FileExistsError(
                f"Output dir {output_dir} exists."
                " Re-running with --force will overwrite existing dir"
            )
        print(f"Docs built and written to {output_dir}")


def main(
    repo_dir,
    package_name,
    geoips_docs_dir,
    output_dir,
    force_overwrite,
    license_url,
    save_temp_dir,
):
    """Prepare for and execute documentation build.

    This function initializes logging, validates paths and package installation,
    logs the configuration, and runs the documentation build process within a temporary
    directory to avoid cluttering the filesystem.

    Parameters
    ----------
    repo_dir : str
        The root directory of the package's repository.
    package_name : str
        The name of the package to build documentation for.
    geoips_docs_dir : str
        The path to the GeoIPS documentation directory (usually geoips/docs)
    output_dir : str
        The directory where the built documentation will be placed.
    save_temp_dir : str
        Optional path to directory to save temp files for reference in debugging
    """
    log = init_logger(True)
    log.debug("Program initialized")

    validate_package_is_installed(package_name, logger=log)

    for path in (
        repo_dir,
        geoips_docs_dir,
        os.path.join(repo_dir, "docs"),
        os.path.join(repo_dir, package_name),
    ):
        validate_path_exists_and_is_git_repo(path, logger=log)

    log.info(f"Repo path is {repo_dir}")
    log.info(f"Repo docs path is {os.path.join(repo_dir, 'docs')}")
    log.info(f"GeoIPS docs path is {geoips_docs_dir}")
    log.info(f"Package name is {package_name}")

    with tempfile.TemporaryDirectory() as docs_build_dir_container:
        build_dir = os.path.join(docs_build_dir_container, "build")
        build_html_docs(
            repo_dir,
            build_dir,
            geoips_docs_dir,
            package_name,
            output_dir,
            force_overwrite,
            license_url,
            log=log,
            save_temp_dir=save_temp_dir,
        )


# Execute the main function with command line arguments
if __name__ == "__main__":
    args = parse_args_with_argparse()
    main(
        repo_dir=args.repo_path,
        package_name=args.package_name,
        geoips_docs_dir=args.geoips_docs_path,
        output_dir=args.output_dir,
        force_overwrite=args.force,
        license_url=args.license_url,
        save_temp_dir=args.save_temp_dir,
    )
