import tempfile
import importlib.util
import warnings
import logging
import logging.handlers
import argparse
import shutil
import os

from rich.logging import RichHandler
from rich.traceback import install as install_rich_tracebacks
import rich_argparse
import pygit2
import jinja2
import sphinx.cmd.build as sphinx_build_module
from sphinx.ext.apidoc import main as sphinx_apidoc


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
    logger = logging.getLogger("build_docs")
    if use_rich:
        install_rich_tracebacks()
        logging_handlers = [RichHandler(rich_tracebacks=True)]
    else:
        logging_handlers = [logging.StreamHandler()]

    logging.basicConfig(level=logging.DEBUG, datefmt="[%X]", handlers=logging_handlers)
    logger.debug("Program initialized")
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
            "Example: build_docs.py /path/to/repo geoips --geoips-version v1.0.0"
        ),
        formatter_class=rich_argparse.RichHelpFormatter,
    )

    # Required positional arguments
    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the repository (e.g., /path/to/geoips). Must be an existing directory.",
    )
    parser.add_argument(
        "package_name",
        type=str,
        help="Name of the package to build (e.g., geoips, data_fusion).",
    )

    # Optional argument: path to documentation templates
    default_docs_path = (
        os.getenv("GEOIPS_PACKAGES_DIR", "") + "/geoips/docs"
        if os.getenv("GEOIPS_PACKAGES_DIR")
        else None
    )
    warnings.warn(
        "GeoIPS docs path defaults to $GEOIPS_PACKAGES_DIR, but this "
        + "fall back is deprecated. Please start passing with "
        + "--geoips-docs-path $GEOIPS_PACKAGES_DIR"
    )
    parser.add_argument(
        "--geoips-docs-path",
        type=str,
        default=default_docs_path,
        help=(
            "Path to GeoIPS documentation templates. "
            "Default is '$GEOIPS_PACKAGES_DIR/geoips/docs' if the environment variable is set."
        ),
    )

    # Optional argument: version (default to 'latest')
    parser.add_argument(
        "--docs-version",
        type=str,
        default="latest",
        help="Version of the package. Default is 'latest'.",
    )

    # Optional argument: version (default to 'latest')
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output dir to write built docs to",
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.output_dir:
        output_dir = os.getenv("GEOIPS_DOCSDIR")
        if output_dir:
            warnings.warn(
                f"Using output dir value {output_dir} from environmental variable "
                + "$GEOIPS_DOCSDIR. This functionality is DEPRECATED and will be"
                + "removed. Please pass $GEOIPS_DOCSDIR as --output-dir $GEOIPS_DOCSDIR "
                + "for the same functionality."
            )
        else:
            output_dir = os.path.join(args.repo_path, "build", "sphinx", "html")
        args.output_dir = output_dir

    return args


def validate_arguments(args):
    """
    Validate input arguments. Must have at least two arguments: repo path and package name.
    """
    # TODO


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

    If the package is not found, it logs a critical error and raises ModuleNotFoundError.

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

    Notes
    -----
    It is unclear WHY this is the placeholder string or what IDX stands for.
    """
    return section.upper() + "IDX"


def get_sections_from_conf_file():
    # TODO
    required_sections = ["releases"]

    optional_sections = [
        "starter",
        "devguide",
        "deployguide",
        "opguide",
        "contact",
    ]

    return required_sections, optional_sections


def return_jinja2_rendered_file_content(template_path):
    """
    Render a Jinja2 template file into a string.

    This function reads the content of the template file, renders it using
    Jinja2, and returns the resulting string.

    Parameters
    ----------
    template_path : str
        The file path to the Jinja2 template.

    Returns
    -------
    str
        The rendered template content as a string.
    """
    with open(template_path, "rt") as template_file:
        return jinja2.Template(template_file.read()).render()


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
    if not is_optional and not os.path.exists(section):
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

    content = return_jinja2_rendered_file_content(template_index_file_path)

    # Replace required sections
    for section in required_sections:
        content = update_content_for_section(build_dir, content, section, log=log)

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
    shutil.copy(
        os.path.join(geoips_docs_dir, "source", "_static"),
        build_dir,
    )
    shutil.copy(
        os.path.join(geoips_docs_dir, "source", "fancyhf.sty"),
        build_dir,
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

    This function copies the package's documentation source files into a build directory.
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

    required_sections, optional_sections = get_sections_from_conf_file()
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
    executes sphinx-apidoc and checks for successful completion.

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
    log.debug(f"Running sphinx apidoc with arguments '{' '.join(arguments)}'")

    if not sphinx_apidoc(arguments) == 0:
        raise Exception("Sphinx API Doc build failed")


def build_docs_with_sphinx(build_dir, built_dir, log=logging.getLogger(__name__)):
    """
    Build documentation HTML files using Sphinx.

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
        # "-W",  # fail on warnings
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


def build_html_docs(
    repo_dir,
    build_dir,
    geoips_docs_dir,
    package_name,
    output_dir,
    log=logging.getLogger(__name__),
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
    log : logging.Logger, optional
        Logger for logging messages; defaults to the module logger.
    """
    log.info("Setting docs files up for building")
    stage_docs_files_for_building(
        os.path.join(repo_dir, "docs", "source"),
        package_name,
        geoips_docs_dir,
        build_dir,
        log=log,
    )

    log.info("Building API docs")
    apidoc_build_path = os.path.join(build_dir, f"{package_name}_api")
    module_path = os.path.join(repo_dir, package_name)  # module path
    build_module_apidocs_with_sphinx(module_path, apidoc_build_path, log=log)

    with tempfile.TemporaryDirectory() as built_dir:
        log.info("Building docs")
        build_docs_with_sphinx(build_dir, built_dir, log=log)
        shutil.copytree(built_dir, output_dir, dirs_exist_ok=True)


def main(repo_dir, package_name, geoips_docs_dir, output_dir, docs_version="latest"):
    """
    Setup and execute documentation build.

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
    docs_version : str, optional
        The version label for the documentation; defaults to "latest".
    """
    log = init_logger(True)

    # validate_package_is_installed(package_name, logger=log)

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
    log.info(f"Version is {docs_version}")

    # generate release notes here, TODO

    with tempfile.TemporaryDirectory() as docs_build_dir_container:
        build_dir = os.path.join(docs_build_dir_container, "build")
        build_html_docs(
            repo_dir, build_dir, geoips_docs_dir, package_name, output_dir, log=log
        )
        log.info(f"Docs built and written to {output_dir}")

    # return_error_codes()


# Execute the main function with command line arguments
if __name__ == "__main__":
    args = parse_args_with_argparse()
    validate_arguments(args)
    main(
        repo_dir=args.repo_path,
        package_name=args.package_name,
        geoips_docs_dir=args.geoips_docs_path,
        output_dir=args.output_dir,
        docs_version=args.docs_version,
    )
