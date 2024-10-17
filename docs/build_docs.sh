# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh
# Build Sphinx doc

echo "***"
echo "GEOIPS_REPO_URL $GEOIPS_REPO_URL"
echo "GEOIPS_PACKAGES_DIR $GEOIPS_PACKAGES_DIR"

if [[ "$1" == "" || "$2" == "" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Must call with repo path and package name.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package [html_only|pdf_only|html_pdf $GEOIPS_PACKAGES_DIR/geoips/docs]"
    echo "***************************************************************************"
    exit 1
fi

which_sphinx=`which sphinx-apidoc`
if [[ "$which_sphinx" == "" ]]; then
    echo "***************************************************************************"
    echo "ERROR: sphinx must be installed prior to building documentation"
    echo "  pip install -e geoips[doc]"
    echo "***************************************************************************"
    exit 1
fi

if [[ ! -d "$1" ]]; then
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
echo "passed path=$1"
repopath=`realpath $1`
docbasepath=$repopath
geoipsdocpath="$GEOIPS_PACKAGES_DIR/geoips/docs"
if [[ ! -d "$docbasepath" ]]; then
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
echo "docbasepath=$docbasepath"

pkgname=$2
echo "pkgname=$pkgname"
if [[ ! -d "$docbasepath/$pkgname" ]]; then
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
echo "package path=$docbasepath/$pkgname"
# Use pip show to determine whether the current package has been installed.
# If the exit status is not zero, the package is not correctly installed.
# In that case, raise an error.
which pip
pip show $pkgname
retval=$?
if [[ "$retval" != "0" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Package $pkgname is not installed"
    echo "***************************************************************************"
    exit 1
else
    echo "***************************************************************************"
    echo "Package $pkgname is already installed!"
    echo "***************************************************************************"
fi

pdf_required="True"
html_required="True"
if [[ "$3" == "html_only" ]]; then
    pdf_required="False"
    html_required="True"
elif [[ "$3" == "pdf_only" ]]; then
    pdf_required="True"
    html_required="False"
fi

echo "pdf_required $pdf_required"
echo "html_required $html_required"

if [[ "$4" != "" ]]; then
    echo "passed geoipsdocpath=$4"
    geoipsdocpath=`realpath $4`
else
    geoipsdocpath="$GEOIPS_PACKAGES_DIR/geoips/docs"
fi
if [[ ! -d "$geoipsdocpath" ]]; then
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
echo "geoips doc path=$geoipsdocpath"
echo "***"

if [[ "$pdf_required" != "True" && "$html_required" != "True" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Did not request pdf or html documentation, quitting."
    echo "***************************************************************************"
    exit 1
fi

if [[ ! -d $docbasepath/build ]]; then
    echo ""
    echo "mkdir -p $docbasepath/build"
    mkdir -p $docbasepath/build
    echo ""
fi

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
if [[ "$git_status_index" == *"docs/source/releases/"*".rst"* ]]; then
    echo "***************************************************************************"
    echo "ERROR: Do not modify docs/source/releases/*.rst directly"
    echo "All RST release files are auto-generated within build_docs.sh using brassy."
    echo "Please revert your changes and try again."
    echo "***************************************************************************"
    exit 1
fi

# Loop through all of the directories in docs/source/releases.
# Each set of YAML release notes is in a single directory, so
# we will build them all into RST release notes prior to building
# the docs.
for version_dir in $docbasepath/docs/source/releases/*/ ; do
    echo $version_dir
    # Only attempt to build release notes from a directory if there
    # are YAML release notes in the directory.
    notes_in_dir=`ls $version_dir/*.yaml`  
    if [[ "$notes_in_dir" == "" ]]; then
        echo "SKIPPING: Empty directory $version_dir, skipping"
        continue
    fi
    # Remove the trailing '/' from the version_dir (the way the
    # directories were listed with /*/ above the trailing '/'
    # is included in the path)
    version=`basename ${version_dir::-1}`
    # Explicitly skip the "upcoming" folder in the documentation.
    # By the time we are ready to include these YAML release notes,
    # they will be moved to the "latest" directory.  "upcoming" only
    # exists during the release process.
    if [[ "$version" == "upcoming" ]]; then
        echo "SKIPPING: Not including 'upcoming' version in documentation."
        continue
    fi

    # Create a temporary file with the header for the release note.
    # This is passed into brassy as the prefix-file.
    RELEASE_NOTE_HEADER=$docbasepath/docs/source/releases/RELEASE_NOTE_HEADER
    touch $RELEASE_NOTE_HEADER
    echo ".. dropdown:: Distribution Statement" >> $RELEASE_NOTE_HEADER
    echo " " >> $RELEASE_NOTE_HEADER
    echo " | This file is auto-generated. Please abide by the license found at" \
    >> $RELEASE_NOTE_HEADER
    echo " | ${GEOIPS_REPO_URL}." \
    >> $RELEASE_NOTE_HEADER

    echo "Running brassy to generate current release note ${version}.rst"
    echo ""
    echo "touch $docbasepath/docs/source/releases/${version}.rst"
    echo "brassy --release-version $version --no-rich \ "
    echo "    --prefix-file $RELEASE_NOTE_HEADER \ "
    echo "    --output-file $docbasepath/docs/source/releases/${version}.rst \ "
    echo "    $docbasepath/docs/source/releases/$version"
    echo "pink $docbasepath/docs/source/releases/${version}.rst"
    echo ""

    # Right now brassy does not auto-generate vers.rst, so we must touch it in
    # advance.
    touch $docbasepath/docs/source/releases/${version}.rst
    # Brassy creates the rst file!
    brassy --release-version $version --no-rich \
        --prefix-file $RELEASE_NOTE_HEADER \
        --output-file $docbasepath/docs/source/releases/${version}.rst \
        $docbasepath/docs/source/releases/${version}
    brassy_retval=$? 
    # Remove the temporary release note header
    rm -f $docbasepath/docs/source/releases/RELEASE_NOTE_HEADER

    # Pinken the RST file
    pink $docbasepath/docs/source/releases/${version}.rst
    pink_retval=$?
    if [[ "$brassy_retval" != "0" || "$pink_retval" != "0" ]]; then
        # Exit here if brassy failed, because the doc build will subsequently fail.
        echo "FAILED brassy ${version}.rst release note generation failed."
        echo "Please resolve release note formatting noted above and retry"
        echo "brassy retval: $brassy_retval"
        echo "pink retval: $pink_retval"
        exit 1
    fi
done

# Ensure index.rst is updated with the latest release notes.
# This will eventually likely be rolled into brassy.
echo "Creating docs/source/releases/index.rst with all release notes"
echo "python $geoipsdocpath/update_release_note_index.py $docbasepath/docs/source/releases/index.rst $docbasepath/docs/source/releases"
python $geoipsdocpath/update_release_note_index.py $docbasepath/docs/source/releases/index.rst $docbasepath/docs/source/releases
if [[ "$?" != "0" ]]; then
    # If this failed, exit here, because doc build will subsequently fail.
    echo "FAILED update_release_note_index.py."
    echo "Please resolve release note formatting noted above and retry"
    exit 1
fi

buildfrom_docpath=$docbasepath/build/buildfrom_docs
echo "buildfrom_docpath=$buildfrom_docpath"

cp -rp $docbasepath/docs $buildfrom_docpath
pdfname="GeoIPS_$pkgname"

echo ""
echo "Building documentation for package: $pkgname"
echo "docbasepath: $docbasepath"
echo "buildfrom_docpath: $buildfrom_docpath"
echo "geoipsdocpath: $geoipsdocpath"
echo ""

# build package conf.py and index.rst, and set PDF name
if [ ! -d "$buildfrom_docpath/source/_templates" ]; then
    mkdir "$buildfrom_docpath/source/_templates"
fi
# Note the full list of sections in the GeoIPS documentation are as defined
# below, and in that explicit order.
# (directory name within docs/source, followed by heading name within index.rst
# in parentheses below):
# * Optional: introduction (Introduction)
# * Optional: starter (Getting Started)
# * Optional: userguide (User Guide)
# * Optional: devguide (Developer Guide)
# * Optional: deployment_guide (Deployment Guide) - note, NOT in geoips repo
# * Optional: operator_guide (Operator Guide) - note, NOT in geoips repo
# * Required: <pkg>_api (API Reference)
# * Required: releases (Release Notes)
# * Optional: contact (Contact)
# Plugin package documentation will follow the same order, only including the
# sections included in their docs/source directory.

# Note api and releases are required for all plugin packages.
# Those are hard coded in source/_templates/index_PKG.html
# introduction, starter, userguide, devguide, and contact are optional -
# if index.rst exist for those sections within a plugin package, include
# them in the main index. If they do not exist, don't include them.
# They are added to index_PKG.html template
# by search/replacing for *IDX in the template below.

# API and releases are NOT included in these search/replace templates,
# since they are hard coded in index_PKG.html, so are required to be included.
introidx="introduction\/index"
startidx="starter\/index"
userguideidx="userguide\/index"
devguideidx="devguide\/index"
deployguideidx="deployguide\/index"
opguideidx="opguide\/index"
contactidx="contact\/index"
# Only include the following links in the index if they exist
if [[ ! -f $docbasepath/docs/source/introduction/index.rst ]]; then
    introidx=""
fi
if [[ ! -f $docbasepath/docs/source/deployguide/index.rst ]]; then
    deployguideidx=""
fi
if [[ ! -f $docbasepath/docs/source/opguide/index.rst ]]; then
    opguideidx=""
fi
if [[ ! -f $docbasepath/docs/source/userguide/index.rst ]]; then
    userguideidx=""
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
echo "sed \"s/PKGNAME/${pkgname}/g\" $geoipsdocpath/source/_templates/conf_PKG.py > $buildfrom_docpath/source/conf.py"
sed "s/PKGNAME/${pkgname}/g" \
    $geoipsdocpath/source/_templates/conf_PKG.py > \
    $buildfrom_docpath/source/conf.py
if [[ "$pkgname" != "geoips" ]]; then
    # need temporary copy of static, format, and foooter for build
    cp -R $geoipsdocpath/source/_static $buildfrom_docpath/source
    cp $geoipsdocpath/source/fancyhf.sty $buildfrom_docpath/source
    cp $geoipsdocpath/source/_templates/geoips_footer.html  \
        $buildfrom_docpath/source/_templates
fi

echo "***"
echo "prerequisite: geoips[doc] installed"
date -u
echo "***"
echo ""

echo "***"
echo "change dir to docbasepath=$docbasepath"
echo "***"
cd $docbasepath

# For now ignoring */lib/* pre-built library directories.  At some point likely want to
# determine how to properly build sphinx api documentation for pre-built libraries, but
# for now ignore them so we can build the API for the rest of the python modules within
# a package. Note the final argument to sphinx-apidoc is the exclude pattern.
echo "***"
echo "sphinx-apidoc -f -T -o $buildfrom_docpath/source/${pkgname}_api $docbasepath/${pkgname} \"*/lib/*\""
echo "***"
sphinx-apidoc -f -T -o $buildfrom_docpath/source/${pkgname}_api $docbasepath/${pkgname} "*/lib/*"

retval_latex="None"
retval_make="None"
# Always touch potential pdf file to support html_only success
echo "***"
echo "touch $buildfrom_docpath/source/${pdfname}.pdf"
echo "***"
touch $buildfrom_docpath/source/${pdfname}.pdf
echo ""
if [[ "$pdf_required" == "True" ]]; then
    which_latex=`which latex`
    if [[ "$which_latex" == "" ]]; then
        echo "ERROR: latex must be installed in order to create pdf documentation."
        echo "  try 'conda install latexcodec' if in anaconda"
        echo "  or re-run with html_only to only build"
        echo "  html documentation."
        exit 1
    fi
    # do not include release notes in the PDF
    # Include starter, contact, devguide if they exist.
    releasidx=""
    sed "s/PKGNAME/${pkgname}/g; s/STARTERIDX/${startidx}/g; \
        s/INTROIDX/${introidx}/g; \
        s/USERGUIDEIDX/${userguideidx}/g; \
        s/CONTACTIDX/${contactidx}/g; \
        s/DEPLOYGUIDEIDX/${deployguideidx}/g; s/OPGUIDEIDX/${opguideidx}/g; \
        s/DEVIDX/${devguideidx}/g; s/RELEASEIDX/${releasidx}/g;" \
        $geoipsdocpath/source/_templates/index_PKG.html > \
        $buildfrom_docpath/source/_templates/indexrst.html
    echo "***"
    echo "building sphinx PDF documentation"
    echo "prerequisite: latex installed"
    date -u
    echo "***"
    echo ""

    echo ""
    echo "temporary mv $buildfrom_docpath/source/releases $buildfrom_docpath"
    mv $buildfrom_docpath/source/releases $buildfrom_docpath

    echo ""
    echo "sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/latex -b latex -W --keep-going"
    output_latex=`sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/latex -b latex -W --keep-going`
    retval_latex=$?
    warnings_latex=`echo "$output_latex" | grep "warnings"`

    echo ""
    echo "restore mv $buildfrom_docpath/releases $buildfrom_docpath/source"
    mv $buildfrom_docpath/releases $buildfrom_docpath/source

    echo ""
    echo "cd $docbasepath/build/sphinx/latex"
    cd $docbasepath/build/sphinx/latex

    echo ""
    echo "make"
    output_make=`make`
    retval_make=$?
    warnings_make=`echo "$output_make" | grep "Latexmk"`

    echo ""
    echo "return to cwd"
    echo "cd -"
    cd -

    echo ""
    echo "$docbasepath/build/sphinx/latex/${pdfname}.pdf $buildfrom_docpath/source/${pdfname}.pdf"
    cp $docbasepath/build/sphinx/latex/${pdfname}.pdf $buildfrom_docpath/source/${pdfname}.pdf
    echo ""
fi

retval_html="None"
if [[ "$html_required" == "True" ]]; then
    # Include release notes in the html doc build (NOT included in pdf)
    releasidx="releases\/index"
    # Include starter, contact, devguide if they exist.
    sed "s/PKGNAME/${pkgname}/g; s/STARTERIDX/${startidx}/g; \
        s/INTROIDX/${introidx}/g; \
        s/USERGUIDEIDX/${userguideidx}/g; \
        s/CONTACTIDX/${contactidx}/g; \
        s/DEPLOYGUIDEIDX/${deployguideidx}/g; s/OPGUIDEIDX/${opguideidx}/g; \
        s/DEVIDX/${devguideidx}/g; s/RELEASEIDX/${releasidx}/g;" \
        $geoipsdocpath/source/_templates/index_PKG.html > \
        $buildfrom_docpath/source/_templates/indexrst.html
    echo "***"
    echo "building sphinx html documentation"
    echo "sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/html -b html -W"
    date -u
    echo "***"
    echo ""
    output_html=`sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/html -b html -W`
    retval_html=$?
    warnings_html=`echo "$output_html" | grep "warnings"`

    echo ""
    echo "***"
    echo "updating permissions on new files and directories"
    date -u
    echo "***"
    echo ""
    find $docbasepath/build/sphinx/html -type d -exec chmod 755 {} \;
    find $docbasepath/build/sphinx/html -type f -exec chmod 644 {} \;
    if [[ "$GEOIPS_DOCSDIR" != "" ]]; then
        echo ""
        echo ""
        echo "copying files into $GEOIPS_DOCS_DIR"
        echo ""
        mkdir -p $GEOIPS_DOCSDIR
        cp -rp $docbasepath/build/sphinx/html/ $GEOIPS_DOCSDIR
    fi
fi

echo ""
echo "***"
date -u
echo "***"
echo ""

echo "Return values:"
echo "  Python install: $retval_install"
echo "  sphinx html:    $retval_html"
echo "  sphinx latex:   $retval_latex"
echo "  latex pdf make: $retval_make"
echo "  warnings html:  $warnings_html"
echo "  warnings latex: $warnings_latex"
echo "  warnings make:  $warnings_make"
retval=$retval_install
if [[ "$retval_html" != "None" ]]; then
    retval=$((retval+retval_html))
fi
if [[ "$retval_latex" != "None" ]]; then
    retval=$((retval+retval_latex))
fi
if [[ "$retval_make" != "None" ]]; then
    retval=$((retval+retval_make))
fi
if [[ "$warnings_latex" != "" ]]; then
    retval=$((retval+1))
fi
if [[ "$warnings_html" != "" ]]; then
    retval=$((retval+1))
fi
echo ""
echo "Final retval: $retval"
exit $retval
