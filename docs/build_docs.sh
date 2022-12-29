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
geoips_package=geoips
if [[ "$1" != "" ]]; then
    geoips_package=$1
fi
docpath=`dirname $0`
if [[ "$2" != "" ]]; then
    docpath=$2
fi
if [[ "$3" != "" ]]; then
    rel=$3
elif [ -z "$GEOIPS_VERS" ]; then
    echo "Must source config_geoips - need GEOIPS_VERS defined"
    exit
else
    rel=$GEOIPS_VERS
fi

modulepath=$docpath/../
echo "$docpath"
echo "$modulepath"
vers=`echo $rel | cut -d . -f 1`.`echo $rel | cut -d . -f 2`
echo "$rel $vers"
echo ""
echo ""
echo "***********************************************"
echo "sphinx-quickstart"
date -u
echo "***********************************************"
echo ""
sphinx-quickstart -p $geoips_package -a nrlmry -v $vers -r $rel -l en --master=index \
                --ext-autodoc --ext-doctest --ext-intersphinx --ext-todo --ext-coverage --ext-imgmath --ext-ifconfig \
                --ext-viewcode --ext-githubpages --extensions=sphinx.ext.napoleon \
                --makefile --no-batchfile -m --sep --dot=_ --suffix='.rst' --epub --ext-mathjax $docpath
echo ""
echo ""
echo "***********************************************"
echo "sphinx-apidoc"
date -u
echo "***********************************************"
echo ""
sphinx-apidoc -o $docpath/source $modulepath
echo ""
echo ""
echo "***********************************************"
echo "copying files into $docpath/source"
date -u
echo "***********************************************"
echo ""
find $modulepath -name '*.rst' \( -not -path "*docs/source*" \) -exec echo cp {} $docpath/source \;
find $modulepath -name '*.rst' \( -not -path "*docs/source*" \) -exec cp {} $docpath/source \;
cp -rp $docpath/images $docpath/source
cp -rp $docpath/yaml $docpath/source
cp $docpath/style.css $docpath/source/_static
cp $docpath/layout.html $docpath/source/_templates
# echo "" >> $docpath/source/conf.py
# echo "" >> $docpath/source/conf.py
# echo "def setup(app):" >> $docpath/source/conf.py
# echo "    app.add_css_file('style.css')" >> $docpath/source/conf.py
mv $docpath/source/${geoips_package}_index.rst $docpath/source/index.rst
echo ""
echo ""
echo "***********************************************"
echo "building sphinx html documentation"
date -u
echo "***********************************************"
echo ""
make -C $docpath html
# make pdf
echo ""
echo ""
echo "***********************************************"
echo "updating permissions on new files and directories"
date -u
echo "***********************************************"
echo ""
find $docpath -type d -exec chmod 755 {} \;
find $docpath -type f -exec chmod 644 {} \;
chmod 755 $docpath/build_docs.sh
if [[ "$GEOIPS_DOCSDIR" != "" ]]; then
    echo ""
    echo ""
    echo "copying files into $GEOIPS_DOCS_DIR"
    echo ""
    mkdir -p $GEOIPS_DOCSDIR
    cp -rp $docpath/build/html/ $GEOIPS_DOCSDIR
fi
