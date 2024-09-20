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
from sphinx.cmd.build import main as sphinx_build
from sphinx.ext.apidoc import main as sphinx_apidoc


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


def parse_args_with_argparse(log=logging.getLogger(__name__)):
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
    log.warning(
        f"GeoIPS docs path defaults to $GEOIPS_PACKAGES_DIR, but this fall back is deprecated. Please start passing with --geoips-docs-path $GEOIPS_PACKAGES_DIR"
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
    # TODO


def validate_path_exists_and_is_git_repo(repo_path, logger=logging.getLogger(__name__)):
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
    Check if the package is installed and available in the same python env as this program is running in
    """
    if importlib.util.find_spec(package_name) is None:
        logger.critical(f"ERROR: Package {package_name} is not installed")
        raise ModuleNotFoundError


def get_section_replace_string(section):
    return section.upper() + "IDX"


def get_sections_from_conf_file():
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
    with open(template_path, "rt") as template_file:
        return jinja2.Template(template_file.read()).render()


def update_content_for_section(
    build_dir, content, section, is_optional=False, log=logging.getLogger(__name__)
):
    section_path = os.path.join(build_dir, section, "index.rst")
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
    arguments = [
        "--no-toc",
        "-o",  # flag for output path
        apidoc_build_path,  # output path
        module_path,  # module path
        "*/lib/*",  # exclude path
    ]
    log.debug(f"Running sphinx apidoc with arguments '{' '.join(arguments)}'")
    sphinx_apidoc(arguments)


def build_docs_with_sphinx(build_dir, built_dir, log=logging.getLogger(__name__)):
    arguments = [
        "-b",  # builder name
        "html",  # uses the html builder
        # "-W",  # fail on warnings
        "-v",
        build_dir,  # folder to build from
        built_dir,  # folder to build to
    ]
    log.debug(f"Running sphinx build with arguments '{' '.join(arguments)}'")
    sphinx_build(arguments)


def build_html_docs(
    repo_dir,
    build_dir,
    geoips_docs_dir,
    package_name,
    log=logging.getLogger(__name__),
):
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


def main(repo_dir, package_name, geoips_docs_dir, docs_version="latest"):
    """
    Main function that drives the entire script execution.
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
        built_dir = build_html_docs(
            repo_dir, build_dir, geoips_docs_dir, package_name, log=log
        )
        # set_file_and_folder_permissions()
        # TODO: copy files if DOCSDIR is set

    # return_error_codes()


# Execute the main function with command line arguments
if __name__ == "__main__":
    args = parse_args_with_argparse()
    validate_arguments(args)
    main(
        repo_dir=args.repo_path,
        package_name=args.package_name,
        geoips_docs_dir=args.geoips_docs_path,
        docs_version=args.docs_version,
    )
