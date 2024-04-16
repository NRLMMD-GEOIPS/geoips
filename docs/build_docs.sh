# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

#!/bin/sh
# Build Sphinx doc

echo "***"
echo "GEOIPS_REPO_URL $GEOIPS_REPO_URL"
echo "GEOIPS_PACKAGES_DIR $GEOIPS_PACKAGES_DIR"

if [[ "$1" == "" || "$2" == "" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Must call with repo path and package name.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package"
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
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package"
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
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package"
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
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin my_package"
    echo "***************************************************************************"
    exit 1
fi
echo "package path=$docbasepath/$pkgname"
echo "***"

pdf_required="True"
html_required="True"
if [[ "$3" == "html_only" ]]; then
    pdf_required="False"
    html_required="True"
fi

echo "pdf_required $pdf_required"
echo "html_required $html_required"

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
startidx="starter\/index"
devguideidx="devguide\/index"
if [[ "$pkgname" != "geoips" ]]; then
    # no starter and devguide for plugins
    startidx=""
    devguideidx=""
fi
echo "sed \"s/PKGNAME/${pkgname}/g\" $geoipsdocpath/source/_templates/conf_PKG.py > $buildfrom_docpath/source/conf.py"
sed "s/PKGNAME/${pkgname}/g" \
    $geoipsdocpath/source/_templates/conf_PKG.py > \
    $buildfrom_docpath/source/conf.py
if [[ "$pkgname" != "geoips" ]]; then
    # need temporary copy of static, contact, format, and foooter for build
    cp -R $geoipsdocpath/source/_static $buildfrom_docpath/source
    cp -R $geoipsdocpath/source/contact $buildfrom_docpath/source
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

echo "***"
echo "sphinx-apidoc $docbasepath/${pkgname} -f -T -o $buildfrom_docpath/source/${pkgname}_api"
echo "***"
sphinx-apidoc $docbasepath/${pkgname} -f -T -o $buildfrom_docpath/source/${pkgname}_api

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
    releasidx=""
    sed "s/PKGNAME/${pkgname}/g; s/STARTERIDX/${startidx}/g; \
        s/DEVIDX/${devguideidx}/g; s/RELEASEIDX/${releasidx}/g;" \
        $geoipsdocpath/docs/source/_templates/index_PKG.html > \
        $buildfrom_docpath/source/_templates/indexrst.html
    echo "***"
    echo "building sphinx PDF documentation"
    echo "prerequisite: latex installed"
    echo "temporary mv $buildfrom_docpath/source/releases $buildfrom_docpath"
    echo "sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/latex -b latex -W"
    echo "restore mv $buildfrom_docpath/releases $buildfrom_docpath/source"
    echo "cd $docbasepath/build/sphinx/latex"
    echo "make"
    echo "cd -"
    date -u
    echo "***"
    echo ""

    mv $buildfrom_docpath/source/releases $buildfrom_docpath
    output_latex=`sphinx-build $buildfrom_docpath/source $docbasepath/build/sphinx/latex -b latex -W`
    retval_latex=$?
    warnings_latex=`echo "$output_latex" | grep "warnings"`
    mv $buildfrom_docpath/releases $buildfrom_docpath/source

    cd $docbasepath/build/sphinx/latex

    output_make=`make`
    retval_make=$?
    warnings_make=`echo "$output_make" | grep "Latexmk"`

    echo "return to cwd"
    cd -

    echo "$docbasepath/build/sphinx/latex/${pdfname}.pdf $buildfrom_docpath/source/${pdfname}.pdf"
    cp $docbasepath/build/sphinx/latex/${pdfname}.pdf $buildfrom_docpath/source/${pdfname}.pdf
fi

retval_html="None"
if [[ "$html_required" == "True" ]]; then
    releasidx="releases\/index"
    sed "s/PKGNAME/${pkgname}/g; s/STARTERIDX/${startidx}/g; \
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
