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

echo "GEOIPS_REPO_URL $GEOIPS_REPO_URL"
echo "GEOIPS_PACKAGES_DIR $GEOIPS_PACKAGES_DIR"

if [[ "$1" == "" ]]; then
    echo "Must call with path to package for documentation build.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips"
    exit 1
fi
docpath=$1
echo "docpath=$docpath"

pdf_required="True"
html_required="True"
if [[ "$2" == "html_only" ]]; then
    pdf_required="False"
    html_required="True"
fi

echo "pdf_required $pdf_required"
echo "html_required $html_required"

if [[ "$pdf_required" != "True" && "$html_required" != "True" ]]; then
    echo "Did not request pdf or html documentation, quitting."
    exit 1
fi

echo "***********************************************"
echo "prerequisite: geoips[doc] installed"
date -u
echo "***********************************************"
echo ""

echo "***********************************************"
echo "change dir to docpath=$docpath"
echo "***********************************************"
cd $docpath

echo "*****************************************************************************"
echo "remove previously generated to clear discontinued modulees"
echo "rm -f $docpath/docs/source/geoips_api/geoips.*"
echo "sphinx-apidoc $docpath/geoips -f -T -o $docpath/docs/source/geoips_api"
echo "*****************************************************************************"
rm -f $docpath/docs/source/geoips_api/geoips.*
sphinx-apidoc $docpath/geoips -f -T -o $docpath/docs/source/geoips_api

retval_latex="None"
retval_make="None"
# Always touch GeoIPS.pdf so the file exists if html_only
echo "***********************************************"
echo "touch $docpath/docs/source/GeoIPS.pdf"
echo "***********************************************"
touch $docpath/docs/source/GeoIPS.pdf
echo ""
if [[ "$pdf_required" == "True" ]]; then
    echo "***********************************************"
    echo "building sphinx PDF documentation"
    echo "prerequisite latex installed"
    echo "try 'module load latex'"
    echo "sphinx-build $docpath/docs/source $docpath/build/sphinx/latex -b latex -W"
    echo "cd $docpath/build/sphinx/latex"
    echo "make"
    echo "cd -"
    date -u
    echo "***********************************************"
    echo ""

    output_latex=`sphinx-build $docpath/docs/source $docpath/build/sphinx/latex -b latex -W`
    retval_latex=$?
    warnings_latex=`echo "$output_latex" | grep "warnings"`

    cd $docpath/build/sphinx/latex

    output_make=`make`
    retval_make=$?
    warnings_make=`echo "$output_make" | grep "Latexmk"`

    echo "return to cwd"
    cd -

    echo "$docpath/build/sphinx/latex/GeoIPS.pdf $docpath/docs/source/GeoIPS.pdf"
    cp $docpath/build/sphinx/latex/GeoIPS.pdf $docpath/docs/source/GeoIPS.pdf
fi

retval_html="None"
if [[ "$html_required" == "True" ]]; then
    echo "***********************************************"
    echo "building sphinx html documentation"
    echo "sphinx-build $docpath/docs/source $docpath/build/sphinx/html -b html -W"
    date -u
    echo "***********************************************"
    echo ""
    output_html=`sphinx-build $docpath/docs/source $docpath/build/sphinx/html -b html -W`
    retval_html=$?
    warnings_html=`echo "$output_html" | grep "warnings"`

    echo ""
    echo "***********************************************"
    echo "updating permissions on new files and directories"
    date -u
    echo "***********************************************"
    echo ""
    find $docpath/build/sphinx/html -type d -exec chmod 755 {} \;
    find $docpath/build/sphinx/html -type f -exec chmod 644 {} \;
    if [[ "$GEOIPS_DOCSDIR" != "" ]]; then
        echo ""
        echo ""
        echo "copying files into $GEOIPS_DOCS_DIR"
        echo ""
        mkdir -p $GEOIPS_DOCSDIR
        cp -rp $docpath/build/sphinx/html/ $GEOIPS_DOCSDIR
    fi
fi

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
