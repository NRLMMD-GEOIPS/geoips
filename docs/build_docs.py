import logging
import argparse
import logging.handlers
import shutil
import os

import rich
from rich.logging import RichHandler
from rich.traceback import install as install_rich_tracebacks
import rich_argparse


def init_logger(use_rich):
    logger = logging.getLogger("build_docs")
    if use_rich:
        install_rich_tracebacks()
        logging_handlers = [RichHandler(rich_tracebacks=True)]
    else:
        logging_handlers = [logging.StreamHandler()]

    logging.basicConfig(level=logging.DEBUG, datefmt="[%X]", handlers=logging_handlers)
    logger.debug("Program initialized")
    return logger


def parse_args():
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
    parser.add_argument(
        "--docs-path",
        type=str,
        default=default_docs_path,
        help=(
            "Path to GeoIPS documentation templates. "
            "Default is '$GEOIPS_PACKAGES_DIR/geoips/docs' if the environment variable is set."
        ),
    )

    # Optional argument: version (default to 'latest')
    parser.add_argument(
        "--set-version",
        type=str,
        default="latest",
        help="Version of the package. Default is 'latest'.",
    )

    # Parse arguments
    args = parser.parse_args()

    return args


def validate_arguments(args):
    """
    Validate input arguments. Must have at least two arguments: repo path and package name.
    """


def print_error_message_for_args():
    """
    Print usage instructions in case of missing arguments.
    """
    print("***************************************************************************")
    print("ERROR: Must call with repo path and package name.  Example usage:")
    print(
        "    ./build_docs.sh path_to_repo package_name [html_only|pdf_only|html_pdf path_to_docs]"
    )
    print("***************************************************************************")


def is_installed_and_in_path(program):
    """
    Return True if provided program is is installed and accessible.
    """
    return shutil.which(program) is not None


def validate_repo_path(repo_path):
    """
    Validate if the repository path exists.
    """
    if not path_exists(repo_path):
        print(f"ERROR: Passed repository path does not exist: {repo_path}")
        exit_script(1)


def validate_package_installation(package_name):
    """
    Check if the package is installed using pip. Exit if not installed.
    """
    # look at this: https://stackoverflow.com/questions/14050281/how-to-check-if-a-python-module-exists-without-importing-it#:~:text=Python%203%20%E2%89%A5%203.4%3A%20importlib.util.find_spec
    result = run_command(f"pip show {package_name}")
    if result.failed:
        print(f"ERROR: Package {package_name} is not installed")
    else:
        print(f"Package {package_name} is already installed!")


def determine_build_requirements(args):
    """
    Determine whether the script should build PDF or HTML documentation based on input arguments.
    """
    # TODO: REMOVE THIS FUNC
    pdf_required = True
    html_required = True
    if len(args) >= 3:
        if args[2] == "html_only":
            pdf_required = False
        elif args[2] == "pdf_only":
            html_required = False
    return pdf_required, html_required


def setup_doc_paths(args):
    """
    Set up the default or custom paths for documentation.
    """
    if len(args) >= 4:
        geoips_doc_path = realpath(args[3])
    else:
        geoips_doc_path = os.getenv("GEOIPS_PACKAGES_DIR") + "/geoips/docs"

    if len(args) >= 5:
        geoips_version = args[4]
    else:
        geoips_version = "latest"

    return geoips_doc_path, geoips_version


def validate_geoips_doc_path(geoips_doc_path):
    """
    Ensure that the geoips doc path exists.
    """
    # TODO: REMOVE FUNC
    if not path_exists(geoips_doc_path):
        print(f"ERROR: GeoIPS docs path does not exist: {geoips_doc_path}")
        exit_script(1)


def create_build_directories(doc_base_path):
    """
    Create the necessary build directories if they don't already exist.
    """
    if not path_exists(f"{doc_base_path}/build"):
        create_directory(f"{doc_base_path}/build")

    if path_exists(f"{doc_base_path}/build/buildfrom_docs"):
        remove_directory(f"{doc_base_path}/build/buildfrom_docs")

    if path_exists(f"{doc_base_path}/build/sphinx"):
        remove_directory(f"{doc_base_path}/build/sphinx")


def check_git_status_index_rst(doc_base_path):
    """
    Check if index.rst has local modifications and raise an error if found.
    """
    git_status = run_command(
        f"git -C {doc_base_path} status docs/source/releases/index.rst"
    )
    if "docs/source/releases/index.rst" in git_status:
        print_separator()
        print("ERROR: Do not modify docs/source/releases/index.rst directly")
        exit_script(1)


def generate_release_notes_if_needed(doc_base_path, geoips_version):
    """
    Generate release notes using brassy if needed.
    """
    current_release_notes = list_directory(
        f"{doc_base_path}/docs/source/releases/latest/*"
    )
    if current_release_notes:
        touch_file(f"{doc_base_path}/docs/source/releases/{geoips_version}.rst")
        run_command(
            f"brassy --release-version {geoips_version} --no-rich --output-file {doc_base_path}/docs/source/releases/{geoips_version}.rst {doc_base_path}/docs/source/releases/latest"
        )
        if not brassy_successful:
            exit_script(1)


def update_release_note_index(geoips_doc_path, doc_base_path, geoips_version):
    """
    Update release note index using Python script.
    """
    run_command(
        f"python {geoips_doc_path}/update_release_note_index.py {doc_base_path}/docs/source/releases/index.rst {geoips_version}"
    )
    if not update_successful:
        exit_script(1)


def build_html_docs_if_required(
    buildfrom_doc_path, doc_base_path, geoips_doc_path, html_required, geoips_doc_dir
):
    """
    Build HTML documentation if required.
    """
    if html_required:
        # Build HTML using Sphinx
        run_command(
            f"sphinx-build {buildfrom_doc_path}/source {doc_base_path}/build/sphinx/html -b html -W"
        )
        # Update file and directory permissions
        update_permissions(doc_base_path)

        # Copy files to GEOIPS_DOCS_DIR if specified
        if geoips_doc_dir:
            copy_files(f"{doc_base_path}/build/sphinx/html/", geoips_doc_dir)


def revert_index_rst(doc_base_path):
    """
    Revert the changes to docs/source/releases/index.rst using Git.
    """
    run_command(f"git -C {doc_base_path} checkout docs/source/releases/index.rst")


def main(repo_path, package_name):
    """
    Main function that drives the entire script execution.
    """
    log = init_logger(True)

    log.info(f"Repo path is {repo_path}")
    log.info(f"Package name is {package_name}")

    for env_var in ["GEOIPS_REPO_URL", "GEOIPS_PACKAGES_DIR"]:
        value = os.getenv(env_var, "UNSET")
        log.debug(f"Environmental variable {env_var} is {value}")

    if not is_installed_and_in_path("sphinx-autodoc"):
        raise ModuleNotFoundError("!")

    check_sphinx_installed()
    validate_repo_path(repo_path)
    validate_package_installation(pkgname)

    raise NotImplementedError("Nothing implemented beyond this")

    pdf_required, html_required = determine_build_requirements(args)
    geoips_doc_path, geoips_version = setup_doc_paths(args)

    validate_geoips_doc_path(geoips_doc_path)
    create_build_directories(repo_path)

    check_git_status_index_rst(repo_path)
    generate_release_notes_if_needed(repo_path, geoips_version)
    update_release_note_index(geoips_doc_path, repo_path, geoips_version)

    build_html_docs_if_required(
        repo_path,
        repo_path,
        geoips_doc_path,
        html_required,
        os.getenv("GEOIPS_DOCSDIR"),
    )

    revert_index_rst(repo_path)

    # Summarize return values and exit
    log.info("Script completed successfully.")


# Execute the main function with command line arguments
if __name__ == "__main__":
    args = parse_args()
    # validate_arguments()
    main(repo_path=args.repo_path, package_name=args.package_name)
