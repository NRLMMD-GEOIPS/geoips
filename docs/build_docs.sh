# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh

echo "***"

echo "GEOIPS_REPO_URL $GEOIPS_REPO_URL"
# Prints the value of the GEOIPS_REPO_URL environment variable.

echo "GEOIPS_PACKAGES_DIR $GEOIPS_PACKAGES_DIR"
# Prints the value of the GEOIPS_PACKAGES_DIR environment variable.

# Check if both positional parameters ($1 and $2) are provided.
if [[ "$1" == "" || "$2" == "" ]]; then
    # If either $1 or $2 is missing, print an error message explaining the required arguments.
    echo "***************************************************************************"
    echo "ERROR: Must call with repo path and package name.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "***************************************************************************"
    # Exit with an error status code 1 because the arguments were missing.
    exit 1
fi

# Check if the sphinx-apidoc tool is installed on the system.
which_sphinx=`which sphinx-apidoc`
if [[ "$which_sphinx" == "" ]]; then
    # If sphinx-apidoc is not found, print an error and provide installation instructions.
    echo "***************************************************************************"
    echo "ERROR: sphinx must be installed prior to building documentation"
    echo "  pip install -e geoips[doc]"
    echo "***************************************************************************"
    exit 1
fi

# Check if the first argument ($1) is a valid directory.
if [[ ! -d "$1" ]]; then
    # If the directory does not exist, print an error message and provide usage examples.
    echo "***************************************************************************"
    echo "ERROR: Passed repository path does not exist."
    echo "       $1"
    echo "ERROR: Must call with repo path and package name.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "***************************************************************************"
    exit 1
fi

# Print the passed repo path.
echo "passed path=$1"

# Get the absolute path of the repo using realpath and store it in repopath.
repopath=`realpath $1`

# Set docbasepath to the value of repopath.
docbasepath=$repopath

# Set geoipsdocpath to the default GEOIPS doc directory path.
geoipsdocpath="$GEOIPS_PACKAGES_DIR/geoips/docs"

# Check if docbasepath is a valid directory.
if [[ ! -d "$docbasepath" ]]; then
    # If not, print an error message and usage instructions.
    echo "***************************************************************************"
    echo "ERROR: Repository 'realpath' does not exist:"
    echo "       $docbasepath"
    echo "ERROR: Must call with repo path and package name.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "***************************************************************************"
    exit 1
fi

# Print the resolved docbasepath.
echo "docbasepath=$docbasepath"

# Set pkgname to the second argument passed to the script.
pkgname=$2
echo "pkgname=$pkgname"

# Check if the package directory exists within the repository.
if [[ ! -d "$docbasepath/$pkgname" ]]; then
    # If the package directory does not exist, print an error message and exit.
    echo "***************************************************************************"
    echo "ERROR: Package path within repository does not exist:"
    echo "       $docbasepath/$pkgname"
    echo "ERROR: Must call with repo path and package name.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "***************************************************************************"
    exit 1
fi

# Print the package path that was checked.
echo "package path=$docbasepath/$pkgname"

# Check if the pip command is available (which pip).
which pip

# Use pip to show information about the package ($pkgname) to verify if it is installed.
pip show $pkgname

# Store the exit status of the pip show command in retval.
retval=$?

# If the package is not installed (retval != 0), print an error and exit.
if [[ "$retval" != "0" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Package $pkgname is not installed"
    echo "***************************************************************************"
    exit 1
else
    # If the package is already installed, print a success message.
    echo "***************************************************************************"
    echo "Package $pkgname is already installed!"
    echo "***************************************************************************"
fi

# Set both pdf and html build flags to "True" by default.
pdf_required="True"
html_required="True"

# If the third argument is "html_only", set pdf_required to "False".
if [[ "$3" == "html_only" ]]; then
    pdf_required="False"
    html_required="True"

# If the third argument is "pdf_only", set html_required to "False".
elif [[ "$3" == "pdf_only" ]]; then
    pdf_required="True"
    html_required="False"
fi

# Print whether PDF and HTML builds are required.
echo "pdf_required $pdf_required"
echo "html_required $html_required"

# If the fourth argument ($4) is provided, use it as the geoipsdocpath.
if [[ "$4" != "" ]]; then
    echo "passed geoipsdocpath=$4"
    geoipsdocpath=`realpath $4`
else
    # Otherwise, set it to the default GeoIPS docs path.
    geoipsdocpath="$GEOIPS_PACKAGES_DIR/geoips/docs"
fi

# If the fifth argument ($5) is provided, use it as the geoips_vers.
if [[ "$5" != "" ]]; then
    echo "passed geoips_vers=$5"
    geoips_vers=$5
else
    # If no version is provided, set geoips_vers to "latest".
    geoips_vers=latest
fi

# Check if the geoipsdocpath is valid.
if [[ ! -d "$geoipsdocpath" ]]; then
    # If not, print an error message and exit.
    echo "***************************************************************************"
    echo "ERROR: GeoIPS docs path, with templates, does not exist:"
    echo "       $geoipsdocpath"
    echo "ERROR: $GEOIPS_PACKAGES_DIR/geoips must exist,"
    echo "       or full path to geoips docs path must be passed in. Ie:"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "***************************************************************************"
    exit 1
fi

# Print the final geoipsdocpath.
echo "geoips doc path=$geoipsdocpath"
echo "***"

# Check if neither PDF nor HTML builds are requested.
if [[ "$pdf_required" != "True" && "$html_required" != "True" ]]; then
    # If so, print an error and exit.
    echo "***************************************************************************"
    echo "ERROR: Did not request pdf or html documentation, quitting."
    echo "***************************************************************************"
    exit 1
fi

# If the build directory does not exist, create it.
if [[ ! -d $docbasepath/build ]]; then
    echo ""
    echo "mkdir -p $docbasepath/build"
    mkdir -p $docbasepath/build
    echo ""
fi

# If the buildfrom_docs directory exists, remove it to avoid conflicts.
if [[ -d $docbasepath/build/buildfrom_docs ]]; then
    echo ""
    echo "***"
    echo "$docbasepath/build/buildfrom_docs exists. Removing to avoid conflicts."
    echo ""
    echo "  rm -rf $docbasepath/build/buildfrom_docs"
    rm -rf $docbasepath/build/buildfrom_docs
    echo "$docbasepath/build/buildfrom_docs removed."
    echo "***"
    echo ""
fi

# If the sphinx build directory exists, remove it to avoid conflicts.
if [[ -d $docbasepath/build/sphinx ]]; then
    echo ""
    echo "***"
    echo "$docbasepath/build/sphinx exists. Removing to avoid conflicts."
    echo ""
    echo "  rm -rf $docbasepath/build/sphinx"
    rm -rf $docbasepath/build/sphinx
    echo "$docbasepath/build/sphinx removed."
    echo "***"
    echo ""
fi

# Since we revert index.rst at the end of this script, make sure the
# user does not have any local modifications before starting.
git_status_index=`git -C $docbasepath status docs/source/releases/index.rst`
# The variable `git_status_index` stores the output of checking the git status of the file
# docs/source/releases/index.rst, which checks if there are any local modifications to this file.

if [[ "$git_status_index" == *"docs/source/releases/index.rst"* ]]; then
    # If there are modifications to the index.rst file (as indicated by the string being found
    # in the git status output), print an error message and exit.
    echo "***************************************************************************"
    echo "ERROR: Do not modify docs/source/releases/index.rst directly"
    echo "Auto-generated within build_docs.sh using brassy."
    echo "Please revert your changes and try again."
    echo "***************************************************************************"
    exit 1
fi

# Release notes are ALWAYS written in the "latest" folder, whether we are
# producing the generic "latest.rst" release note, or the specific
# vX_Y_Z.rst release note for an actual version release.
current_release_notes=`ls $docbasepath/docs/source/releases/latest/*`
# The variable `current_release_notes` stores the list of release notes files in the latest folder.

# If there are any release notes found, proceed to generate the release note RST file.
if [[ "$current_release_notes" != "" ]]; then
    # If the release notes are found, print a message that brassy will be used to generate
    # the release note for the specified version.
    echo "Running brassy to generate current release note ${geoips_vers}.rst"
    echo ""
    echo "touch $docbasepath/docs/source/releases/${geoips_vers}.rst"
    echo "brassy --release-version $geoips_vers --no-rich \"
    echo "    --output-file $docbasepath/docs/source/releases/${geoips_vers}.rst \"
    echo "    $docbasepath/docs/source/releases/latest"
    echo ""

    # Create an empty file for the release notes using touch to ensure the file exists.
    touch $docbasepath/docs/source/releases/${geoips_vers}.rst
    # Run brassy, a documentation tool, to generate the release notes in the specified file.
    brassy --release-version $geoips_vers --no-rich \
        --output-file $docbasepath/docs/source/releases/${geoips_vers}.rst \
        $docbasepath/docs/source/releases/latest

    # Check if the brassy command executed successfully.
    if [[ "$?" != "0" ]]; then
        # If brassy failed, print an error message and exit.
        echo "FAILED brassy ${geoips_vers}.rst release note generation failed."
        echo "Please resolve release note formatting noted above and retry"
        exit 1
    fi

    # Ensure index.rst is updated with the latest release notes.
    # This will eventually likely be rolled into brassy.
    echo "Adding latest section to release note index"
    # Run a Python script to update the index with the latest release notes.
    echo "python $geoipsdocpath/update_release_note_index.py $docbasepath/docs/source/releases/index.rst $geoips_vers"
    python $geoipsdocpath/update_release_note_index.py $docbasepath/docs/source/releases/index.rst $geoips_vers

    # Check if the Python script ran successfully.
    if [[ "$?" != "0" ]]; then
        # If the Python script failed, print an error message and exit.
        echo "FAILED update_release_note_index.py for version ${geoips_vers}"
        echo "Please resolve release note formatting noted above and retry"
        exit 1
    fi
fi

# Set the path for buildfrom_docs, where the docs will be built from.
buildfrom_docpath=$docbasepath/build/buildfrom_docs
echo "buildfrom_docpath=$buildfrom_docpath"

# Copy the docs directory to the buildfrom_docs directory to create a working copy.
cp -rp $docbasepath/docs $buildfrom_docpath

# Set the name of the PDF file that will be generated.
pdfname="GeoIPS_$pkgname"

echo ""
# Print messages indicating the start of the documentation build process.
echo "Building documentation for package: $pkgname"
echo "docbasepath: $docbasepath"
echo "buildfrom_docpath: $buildfrom_docpath"
echo "geoipsdocpath: $geoipsdocpath"
echo ""

# Check if the _templates directory does not exist in the source folder. If not, create it.
if [ ! -d "$buildfrom_docpath/source/_templates" ]; then
    mkdir "$buildfrom_docpath/source/_templates"
fi

# The next section of comments explains that the structure and sections of the GeoIPS documentation
# are defined in a specific order, with certain sections being required and others optional.
# The order is Introduction, Getting Started, User Guide, Developer Guide, etc.

# Set index template variables for the optional sections.
startidx="starter\/index"
devguideidx="devguide\/index"
deployguideidx="deployguide\/index"
opguideidx="opguide\/index"
contactidx="contact\/index"

# Check if each optional section exists, and if not, set the corresponding variable to an empty string.
if [[ ! -f $docbasepath/docs/source/deployguide/index.rst ]]; then
    deployguideidx=""
fi
if [[ ! -f $docbasepath/docs/source/opguide/index.rst ]]; then
    opguideidx=""
fi
if [[ ! -f $docbasepath/docs/source/starter/index.rst ]]; then
    startidx=""
fi
if [[ ! -f $docbasepath/docs/source/devguide/index.rst ]]; then
    devguideidx=""
fi
if [[ ! -f $docbasepath/docs/source/contact/index.rst ]]; then
    contactidx=""
fi

# Use sed (stream editor) to replace placeholder variables (PKGNAME, STARTERIDX, etc.) with actual values
# in the conf_PKG.py template. This configures the Sphinx build.
echo "sed \"s/PKGNAME/${pkgname}/g\" $geoipsdocpath/source/_templates/conf_PKG.py > $buildfrom_docpath/source/conf.py"
sed "s/PKGNAME/${pkgname}/g" \
    $geoipsdocpath/source/_templates/conf_PKG.py > \
    $buildfrom_docpath/source/conf.py

# If the package name is not "geoips", copy additional static files and templates to the build directory.
if [[ "$pkgname" != "geoips" ]]; then
    # Copy the _static directory to the source folder.
    cp -R $geoipsdocpath/source/_static $buildfrom_docpath/source
    # Copy a LaTeX style file.
    cp $geoipsdocpath/source/fancyhf.sty $buildfrom_docpath/source
    # Copy a footer template for HTML documentation.
    cp $geoipsdocpath/source/_templates/geoips_footer.html  \
        $buildfrom_docpath/source/_templates
fi

# Print the current date and time in UTC for tracking purposes.
echo "***"
echo "prerequisite: geoips[doc] installed"
date -u
echo "***"
echo ""

# Change the current working directory to the docbasepath.
echo "***"
echo "change dir to docbasepath=$docbasepath"
echo "***"
cd $docbasepath

# Build the Sphinx API documentation, excluding pre-built libraries in the "lib" directories.
# The "-f" flag forces overwriting existing files, and "-T" shows the full traceback on error.
echo "***"
echo "sphinx-apidoc -f -T -o $buildfrom_docpath/source/${pkgname}_api $docbasepath/${pkgname} \"*/lib/*\""
echo "***"
sphinx-apidoc -f -T -o $buildfrom_docpath/source/${pkgname}_api $docbasepath/${pkgname} "*/lib/*"

# Initialize variables for tracking the return values of the LaTeX and make processes.
retval_latex="None"
retval_make="None"

# Always touch (create if it doesn't exist) the potential PDF file to support html-only success.
echo "***"
echo "touch $buildfrom_docpath/source/${pdfname}.pdf"
echo "***"
touch $buildfrom_docpath/source/${pdfname}.pdf

# If PDF documentation is required, check if LaTeX is installed.
if [[ "$pdf_required" == "True" ]]; then
    which_latex=`which latex`
    if [[ "$which_latex" == "" ]]; then
        # If LaTeX is not installed, print an error message and exit.
        echo "ERROR: latex must be installed in order to create pdf documentation."
        echo "  try 'conda install latexcodec' if in anaconda"
        echo "  or re-run with html_only to only build"
        echo "  html documentation."
        echo ""
        # Revert changes made to index.rst.
        echo "Reverting $docbasepath/docs/source/releases/index.rst"
        git -C $docbasepath checkout docs/source/releases/index.rst
        exit 1
    fi

    # Do not include release notes in the PDF build.
    releasidx=""
    # Use sed to replace placeholders in the index_PKG.html template for building the documentation.
    sed "s/PKGNAME/${pkgname}/g; s/STARTERIDX/${startidx}/g; \
        s/CONTACTIDX/${contactidx}/g; \
        s/DEPLOYGUIDEIDX/${deployguideidx}/g; s/OPGUIDEIDX/${opguideidx}/g; \
        s/DEVIDX/${devguideidx}/g; s/RELEASEIDX/${releasidx}/g;" \
        $geoipsdocpath/source/_templates/index_PKG.html > \
        $buildfrom_docpath/source/_templates/indexrst.html

    # Print information about the PDF build process and LaTeX installation.
    echo "***"
    echo "building sphinx PDF documentation"
    echo "prerequisite: latex installed"
    date -u
    echo "***"
    echo ""

    # Temporarily move the release notes directory to avoid including it in the PDF build.
    echo ""
    echo "temporary mv $buildfrom_docpath/source/releases $buildfrom_docpath"
    mv $buildfrom_docpath/source/releases $buildfrom_docpath

    # Run Sphinx to build the LaTeX documentation from the source directory.
    echo ""
    echo "sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/latex -b latex -W --keep-going"
    output_latex=`sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/latex -b latex -W --keep-going`
    retval_latex=$?
    # Capture any warnings from the LaTeX build output.
    warnings_latex=`echo "$output_latex" | grep "warnings"`

    # Move the release notes directory back after the LaTeX build is complete.
    echo ""
    echo "restore mv $buildfrom_docpath/releases $buildfrom_docpath/source"
    mv $buildfrom_docpath/releases $buildfrom_docpath/source

    # Change directory to where the LaTeX files were built.
    echo ""
    echo "cd $docbasepath/build/sphinx/latex"
    cd $docbasepath/build/sphinx/latex

    # Run the make command to compile the LaTeX files into a PDF.
    echo ""
    echo "make"
    output_make=`make`
    retval_make=$?
    # Capture any warnings from the make command output.
    warnings_make=`echo "$output_make" | grep "Latexmk"`

    # Return to the previous working directory after the make process is done.
    echo ""
    echo "return to cwd"
    echo "cd -"
    cd -

    # Copy the generated PDF back to the source directory.
    echo ""
    echo "$docbasepath/build/sphinx/latex/${pdfname}.pdf $buildfrom_docpath/source/${pdfname}.pdf"
    cp $docbasepath/build/sphinx/latex/${pdfname}.pdf $buildfrom_docpath/source/${pdfname}.pdf
    echo ""
fi

# Check if HTML documentation is required.
retval_html="None"
if [[ "$html_required" == "True" ]]; then
    # Include release notes in the HTML doc build (which were excluded from the PDF).
    releasidx="releases\/index"
    # Include starter, contact, devguide if they exist.
    # Use sed to replace the placeholders in the HTML index template with actual values.
    sed "s/PKGNAME/${pkgname}/g; s/STARTERIDX/${startidx}/g; \
        s/CONTACTIDX/${contactidx}/g; \
        s/DEPLOYGUIDEIDX/${deployguideidx}/g; s/OPGUIDEIDX/${opguideidx}/g; \
        s/DEVIDX/${devguideidx}/g; s/RELEASEIDX/${releasidx}/g;" \
        $geoipsdocpath/source/_templates/index_PKG.html > \
        $buildfrom_docpath/source/_templates/indexrst.html

    # Print a message indicating the start of the HTML documentation build process.
    echo "***"
    echo "building sphinx html documentation"
    echo "sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/html -b html -W"
    date -u
    echo "***"
    echo ""

    # Run Sphinx to build the HTML documentation from the source directory.
    # The output is stored in `output_html`, and the exit status is stored in `retval_html`.
    output_html=`sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/html -b html -W`
    retval_html=$?
    # Capture any warnings generated during the HTML build process.
    warnings_html=`echo "$output_html" | grep "warnings"`

    # Update the permissions on the newly generated files and directories.
    echo ""
    echo "***"
    echo "updating permissions on new files and directories"
    date -u
    echo "***"
    echo ""

    # Set the directory permissions to 755 for all directories in the HTML build folder.
    find $docbasepath/build/sphinx/html -type d -exec chmod 755 {} \;
    # Set the file permissions to 644 for all files in the HTML build folder.
    find $docbasepath/build/sphinx/html -type f -exec chmod 644 {} \;

    # If the GEOIPS_DOCSDIR environment variable is set, copy the built HTML files to the specified directory.
    if [[ "$GEOIPS_DOCSDIR" != "" ]]; then
        echo ""
        echo ""
        echo "copying files into $GEOIPS_DOCS_DIR"
        echo ""
        # Create the destination directory if it doesn't already exist.
        mkdir -p $GEOIPS_DOCSDIR
        # Copy the HTML files into the destination directory.
        cp -rp $docbasepath/build/sphinx/html/ $GEOIPS_DOCSDIR
    fi
fi

# Revert the changes made to the `index.rst` file, restoring its original state.
echo ""
echo "***"
# docs/source/releases/index.rst should only be auto-generated,
# so revert the changes we just made.  Note we checked at the beginning
# if this was already modified, and exited if there were any local modifications,
# to ensure the user had not manually modified it.
# git -C $docbasepath status docs/source/releases/index.rst
echo "Reverting $docbasepath/docs/source/releases/index.rst"
# Use git to revert any local modifications made to the `index.rst` file.
git -C $docbasepath checkout docs/source/releases/index.rst
# Print the current date in UTC after reverting the file.
date -u
echo "***"
echo ""

# Print out the return values from the various processes (installation, HTML build, LaTeX build, and PDF make).
echo "Return values:"
echo "  Python install: $retval_install"
echo "  sphinx html:    $retval_html"
echo "  sphinx latex:   $retval_latex"
echo "  latex pdf make: $retval_make"
echo "  warnings html:  $warnings_html"
echo "  warnings latex: $warnings_latex"
echo "  warnings make:  $warnings_make"

# Initialize `retval` to the value of the Python installation return value.
retval=$retval_install
# If there was an HTML build result, add its exit status to the `retval` variable.
if [[ "$retval_html" != "None" ]]; then
    retval=$((retval+retval_html))
fi
# If there was a LaTeX build result, add its exit status to the `retval` variable.
if [[ "$retval_latex" != "None" ]]; then
    retval=$((retval+retval_latex))
fi
# If there was a PDF make result, add its exit status to the `retval` variable.
if [[ "$retval_make" != "None" ]]; then
    retval=$((retval+retval_make))
fi
# If there were any LaTeX warnings, increment `retval` by 1.
if [[ "$warnings_latex" != "" ]]; then
    retval=$((retval+1))
fi
# If there were any HTML warnings, increment `retval` by 1.
if [[ "$warnings_html" != "" ]]; then
    retval=$((retval+1))
fi

# Print the final return value after aggregating all results.
echo ""
echo "Final retval: $retval"
# Exit the script with the final return value, indicating success or failure.
exit $retval