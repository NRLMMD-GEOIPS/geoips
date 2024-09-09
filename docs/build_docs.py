# Import necessary modules like os, subprocess, and sys for system operations


def print_separator():
    """
    Function to print a separator of asterisks for visual clarity.
    """
    print("***")


def validate_arguments(args):
    """
    Validate input arguments. Must have at least two arguments: repo path and package name.
    """
    if len(args) < 2:
        print_separator()
        print_error_message_for_args()
        exit_script(1)


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


def check_sphinx_installed():
    """
    Check if sphinx-apidoc is installed. If not, exit the script with an error.
    """
    sphinx_path = run_command("which sphinx-apidoc")
    if not sphinx_path:
        print_separator()
        print("ERROR: sphinx must be installed prior to building documentation")
        print("  pip install -e geoips[doc]")
        print_separator()
        exit_script(1)


def validate_repo_path(repo_path):
    """
    Validate if the repository path exists.
    """
    if not path_exists(repo_path):
        print_separator()
        print(f"ERROR: Passed repository path does not exist: {repo_path}")
        print_separator()
        exit_script(1)


def realpath(path):
    """
    Get the absolute real path of the given directory.
    """
    # Simulate a realpath function
    return os.path.abspath(path)


def validate_package_installation(package_name):
    """
    Check if the package is installed using pip. Exit if not installed.
    """
    result = run_command(f"pip show {package_name}")
    if result.failed:
        print_separator()
        print(f"ERROR: Package {package_name} is not installed")
        print_separator()
        exit_script(1)
    else:
        print_separator()
        print(f"Package {package_name} is already installed!")
        print_separator()


def determine_build_requirements(args):
    """
    Determine whether the script should build PDF or HTML documentation based on input arguments.
    """
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
    if not path_exists(geoips_doc_path):
        print_separator()
        print(f"ERROR: GeoIPS docs path does not exist: {geoips_doc_path}")
        print_separator()
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


def build_pdf_docs_if_required(
    buildfrom_doc_path, doc_base_path, pkgname, pdf_required
):
    """
    Build PDF documentation if required, and check for LaTeX installation.
    """
    if pdf_required:
        latex_installed = run_command("which latex")
        if not latex_installed:
            print("ERROR: LaTeX must be installed to build PDFs.")
            revert_index_rst(doc_base_path)
            exit_script(1)

        # Build LaTeX using Sphinx
        run_command(
            f"sphinx-build {buildfrom_doc_path}/source {doc_base_path}/build/sphinx/latex -b latex -W --keep-going"
        )

        # Run make to build the PDF from LaTeX files
        run_command(f"cd {doc_base_path}/build/sphinx/latex && make")
        if make_failed:
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


def exit_script(return_value):
    """
    Exit the script with a specific return value.
    """
    print(f"Exiting with status: {return_value}")
    sys.exit(return_value)


# Main function that coordinates the flow
def main(args):
    """
    Main function that drives the entire script execution.
    """
    print_separator()
    validate_arguments(args)

    repo_path = realpath(args[0])
    pkgname = args[1]

    check_sphinx_installed()
    validate_repo_path(repo_path)
    validate_package_installation(pkgname)

    pdf_required, html_required = determine_build_requirements(args)
    geoips_doc_path, geoips_version = setup_doc_paths(args)

    validate_geoips_doc_path(geoips_doc_path)
    create_build_directories(repo_path)

    check_git_status_index_rst(repo_path)
    generate_release_notes_if_needed(repo_path, geoips_version)
    update_release_note_index(geoips_doc_path, repo_path, geoips_version)

    build_pdf_docs_if_required(repo_path, repo_path, pkgname, pdf_required)
    build_html_docs_if_required(
        repo_path,
        repo_path,
        geoips_doc_path,
        html_required,
        os.getenv("GEOIPS_DOCSDIR"),
    )

    revert_index_rst(repo_path)

    # Summarize return values and exit
    print("Script completed successfully.")
    exit_script(0)


# Execute the main function with command line arguments
if __name__ == "__main__":
    main(sys.argv[1:])
