import tempfile
import importlib.util
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


def parse_args_with_argparse():
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


def path_exists_and_is_git_repo(repo_path, logger=logging.getLogger(__name__)):
    if not os.path.exists(repo_path):
        logger.critical(f"Path does not exist: {repo_path}")
        raise FileNotFoundError
    try:
        pygit2.Repository(repo_path)
    except pygit2.GitError as e:
        logger.critical(f"{repo_path} is not a valid git repo")
        raise e


def validate_package_installation(package_name, logger=logging.getLogger(__name__)):
    """
    Check if the package is installed and available in the same python env as this program is running in
    """
    if importlib.util.find_spec(package_name) is None:
        logger.critical(f"ERROR: Package {package_name} is not installed")
        raise ModuleNotFoundError


def main(docs_base_path, package_name, geoips_docs_path, docs_version="latest"):
    """
    Main function that drives the entire script execution.
    """
    log = init_logger(True)

    for env_var in ["GEOIPS_REPO_URL", "GEOIPS_PACKAGES_DIR"]:
        value = os.getenv(env_var, "UNSET")
        if value == "UNSET":
            logger = log.warning
        else:
            logger = log.debug
        logger(f"Environmental variable {env_var} is {value}")

    if not is_installed_and_in_path("sphinx-autodoc"):
        # raise ModuleNotFoundError("!")  # better errors
        pass

    # validate_package_installation(package_name, logger=log)
    docs_path = os.path.join(docs_base_path, "docs")

    for path in (
        docs_base_path,
        docs_path,
        geoips_docs_path,
        os.path.join(docs_base_path, package_name),
    ):
        path_exists_and_is_git_repo(docs_base_path, logger=log)

    log.info(f"Repo path is {docs_base_path}")
    log.info(f"Repo docs path is {docs_path}")
    log.info(f"GeoIPS docs path is {geoips_docs_path}")
    log.info(f"Package name is {package_name}")
    log.info(f"Version is {docs_version}")

    """
    docs_build_dir = os.path.join(docs_base_path, "build")
    os.makedirs(docs_build_dir, exist_ok=True)

    for d in [
        os.path.join(docs_build_dir, sub_path)
        for sub_path in ["buildfrom_docs", "sphinx"]
    ]:
        try:
            shutil.rmtree(d)
        except FileNotFoundError:
            pass
    """

    # generate release notes here, TODO

    with tempfile.TemporaryDirectory() as docs_build_dir_container:
        docs_build_dir = os.path.join(docs_build_dir_container, "build")
        shutil.copytree(docs_path, docs_build_dir)
        build_docs_source_dir = os.path.join(docs_path, "source")
        template_path = os.path.join(docs_build_dir, "source", "_templates")
        os.makedirs(template_path, exist_ok=True)
        if not package_name == "geoips":
            shutil.copy(
                os.path.join(geoips_docs_path, "source", "_static"),
                build_docs_source_dir,
            )
            shutil.copy(
                os.path.join(geoips_docs_path, "source", "fancyhf.sty"),
                build_docs_source_dir,
            )
            shutil.copy(
                os.path.join(
                    geoips_docs_path, "source", "_templates", "geoips_footer.html"
                ),
                template_path,
            )

        template_conf_file_path = os.path.join(
            geoips_docs_path, "source", "_templates", "sphinx_conf.template.py"
        )
        build_conf_file_path = os.path.join(build_docs_source_dir, "conf.py")

        with open(template_conf_file_path, "rt") as template_conf_file:
            with open(build_conf_file_path, "wt") as build_conf_file:
                for line in template_conf_file:
                    build_conf_file.write(line.replace("PKGNAME", package_name))

        log.info("Docs build files setup")
        log.info("Building docs")
        # setup_optional_sections()

        required_sections = ["releases"]

        optional_sections = [
            "starter",
            "devguide",
            "deployguide",
            "opguide",
            "contact",
        ]

        template_index_file_path = os.path.join(
            geoips_docs_path, "source", "_templates", "index.template.rst"
        )
        build_index_file_path = os.path.join(build_docs_source_dir, "index.rst")

        def get_section_replace_string(section):
            return section.upper() + "IDX"

        with open(template_index_file_path, "rt") as template_index_file:
            with open(build_index_file_path, "wt") as build_index_file:
                content = jinja2.Template(template_index_file.read()).render()
                for section in required_sections:
                    content = content.replace(
                        get_section_replace_string(section), f"{section}/index"
                    )
                for section in optional_sections:
                    if os.path.exists(
                        os.path.join(build_docs_source_dir, section, "index.rst")
                    ):
                        log.debug(f"Including optional section {section}")
                        content = content.replace(
                            get_section_replace_string(section), f"{section}/index"
                        )
                    else:
                        log.debug(f"Removing optional section {section}")
                        content = content.replace(
                            get_section_replace_string(section), ""
                        )
                content = content.replace("PKGNAME", package_name)
                print(content)
                build_index_file.write(content)

        from sphinx.ext.apidoc import main as sphinx_apidoc

        log.info("Building API docs")
        apidoc_build_path = os.path.join(
            docs_build_dir, "source", f"{package_name}_api"
        )
        arguments = [
            # "--force",  # overwrite existing files
            "--no-toc",
            "-o",
            apidoc_build_path,  # output path
            os.path.join(docs_base_path, package_name),  # module path
            "*/lib/*",  # exclude path
        ]
        log.debug(f"Running sphinx apidoc with arguments '{' '.join(arguments)}'")
        sphinx_apidoc(arguments)

        from sphinx.cmd.build import main as sphinx_build

        with tempfile.TemporaryDirectory() as docs_build_final:
            docs_build_final_dir = os.path.join(docs_build_final, "build")
            log.info("Building docs")
            sphinx_source = os.path.join(docs_build_dir, "source")
            arguments = [
                "-b",  # builder name
                "html",  # uses the html builder
                # "-W",  # fail on warnings
                "-v",
                sphinx_source,
                docs_build_final_dir,
            ]
            log.debug(f"Running sphinx build with arguments '{' '.join(arguments)}'")
            sphinx_build(arguments)
            exit(1)
        raise NotImplementedError("Nothing implemented beyond this")

        # set_file_and_folder_permissions()
        # TODO: copy files if DOCSDIR is set

    return_error_codes()


# Execute the main function with command line arguments
if __name__ == "__main__":
    args = parse_args_with_argparse()
    # validate_arguments()
    main(
        docs_base_path=args.repo_path,
        package_name=args.package_name,
        geoips_docs_path=args.geoips_docs_path,
        docs_version=args.docs_version,
    )
