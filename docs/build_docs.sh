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
# * Required: introduction (Introduction)
# * Optional: starter (Getting Started)
# * Required: userguide (User Guide)
# * Optional: devguide (Developer Guide)
# * Optional: deployment_guide (Deployment Guide) - note, NOT in geoips repo
# * Optional: operator_guide (Operator Guide) - note, NOT in geoips repo
# * Required: <pkg>_api (API Reference)
# * Required: releases (Release Notes)
# * Optional: contact (Contact)
# Plugin package documentation will follow the same order, only including the
# sections included in their docs/source directory.

# Note api, introduction, and userguide are required for all plugin packages.
# Those are hard coded in source/_templates/index_PKG.html
# starter, devguide, and contact are optional - if index.rst exist for those
# sections within a plugin package, include them in the main index. If they
# do not exist, don't include them.  They are added to index_PKG.html template
# by search/replacing for *IDX in the template below.
startidx="starter\/index"
devguideidx="devguide\/index"
deployguideidx="deployguide\/index"
opguideidx="opguide\/index"
contactidx="contact\/index"
# Only include the following links in the index if they exist
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
