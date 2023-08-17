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
# Deploy Sphinx doc to GitHub Pages
echo "***"
echo "Requires docs/build_docs.sh run first"
echo "Will create/update/push ghpages branch"
echo "***"

echo "GEOIPS_REPO_URL $GEOIPS_REPO_URL"
echo "GEOIPS_PACKAGES_DIR $GEOIPS_PACKAGES_DIR"

if [[ "$1" == "" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Must call with repo path.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin"
    echo "***************************************************************************"
    exit 1
fi

if [[ -z "$GEOIPS_REPO_URL" ]]; then
    echo ""
    echo "***************************************************************************"
    echo "Must define GEOIPS_REPO_URL environment variable prior to deploying pages"
    echo "ie:"
    echo ""
    echo "  export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS"
    echo "***************************************************************************"
    echo ""
    exit 1
fi
if [[ ! -d "$1" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Passed repository path does not exist."
    echo "       $1"
    echo "ERROR: Must call with repo path.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin"
    echo "***************************************************************************"
    exit 1
fi

# Expected that build_docs.sh has already been run.
# Keep documentation build and deploy separate steps.
repopath=`realpath $1`
if [[ ! -d "$repopath" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Repository 'realpath' does not exist:"
    echo "       $repopath"
    echo "ERROR: Must call with repo path.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin"
    echo "***************************************************************************"
    exit 1
fi
docpath=$repopath/build/sphinx/html

echo "docpath=$docpath"

reponame=`basename $repopath`

if [[ ! -d $docpath ]]; then
    echo ""
    echo "***************************************************************************"
    echo "ERROR: Pre-built html documentation does not exist."
    echo "Ensure you successfully run build_docs.sh prior to deploy_pages.sh"
    echo ""
    echo "  $GEOIPS_PACKAGES_DIR/geoips/build_docs.sh $1 <package_name>"
    echo "  $GEOIPS_PACKAGES_DIR/geoips/deploy_pages.sh $1"
    echo "***************************************************************************"
    echo ""
    exit 1
fi

pagespath=$GEOIPS_PACKAGES_DIR/pages/$reponame

if [[ ! -d $pagespath ]]; then
    echo "***"
    echo "Cloning $reponame repo"
    echo "git clone $GEOIPS_REPO_URL/$reponame $pagespath"
    echo "***"
    git clone $GEOIPS_REPO_URL/$reponame $pagespath
    clone_retval=$?
    if [[ "$clone_retval" != "0" ]]; then
        echo "***********************************************************************"
        echo "ERROR: git clone failed!  Quitting."
        echo "***********************************************************************"
        exit 1
    fi
fi

if [[ ! -d $pagespath ]]; then
    echo "***************************************************************************"
    echo "ERROR: ghpages directory does not exist!  Quitting."
    echo "***************************************************************************"
    exit 1
fi

echo "***"
echo "Update to ghpages branch"
echo "git -C $pagespath fetch --all -p"
echo "git -C $pagespath checkout ghpages"
echo "git -C $pagespath pull"
echo "***"

git -C $pagespath fetch --all -p

git -C $pagespath checkout ghpages
checkout_retval=$?
if [[ "$checkout_retval" != 0 ]]; then
    echo "***********************************************************************"
    echo "ERROR: git checkout failed!  Quitting."
    echo "***********************************************************************"
    exit 1
fi

git -C $pagespath pull
pull_retval=$?
if [[ "$pull_retval" != 0 ]]; then
    echo "***********************************************************************"
    echo "ERROR: git pull failed!  Quitting."
    echo "***********************************************************************"
    exit 1
fi

echo "***"
echo "remove previously generated to clear discontinued modules"
echo "rm -rf $pagespath/docs/*"
echo "cp -R $docpath/*"
echo "      $pagespath/docs"
echo "***"
rm -rf $pagespath/docs/*
if [[ ! -d $pagespath/docs ]]; then
    echo "***"
    echo "mkdir $pagespath/docs"
    mkdir $pagespath/docs
    echo "***"
fi
cp -R $docpath/* $pagespath/docs
if [[ ! -f $pagespath/docs/.nojekyll ]]; then
    # .nojekyll ensures github pages does not attempt to use jekyll themes for
    # rendering the html.  This file should already exist in the docs directory
    # (and not be deleted with the rm -rf docs/* above, since it is hidden), but
    # touch included here for insurance.  When .nojekyll does not exist, no
    # style information is available (since jekyll ignores _* directories),
    # so the html rendering is very ugly.
    echo "***"
    echo "Ensure .nojekyll file exists for proper github pages rendering"
    echo "touch $pagespath/docs/.nojekyll"
    touch $pagespath/docs/.nojekyll
    echo "***"
fi

echo "***"
echo "Adding new/updated files"
echo "git -C $pagespath add docs"
echo "git -C $pagespath status"
echo "***"
git -C $pagespath add docs
git -C $pagespath status

echo "***"
echo "Set git status for obtaining current branch"
echo "gstatus=(\`git -C $repopath status\`)"
gstatus=(`git -C $repopath status`)
echo "$gstatus"
echo "***"

echo "***"
echo "Commit/push new/updated sphinx html files to ghpages branch"
echo "git -C $pagespath commit -m 'sphinx html for github pages from: ${gstatus[2]}'"
echo "git -C $pagespath push origin ghpages"
echo "***"

commit_output=`git -C $pagespath commit -m "sphinx html for github pages from: ${gstatus[2]}"`
commit_retval=$?
echo $commit_output
if [[ "$commit_retval" != 0 ]]; then
    if [[ "$commit_output" == *"nothing to commit, working tree clean"* ]]; then
        echo "***"
        echo "No new files to commit"
        echo "***"
    else
        echo "***********************************************************************"
        echo "ERROR: git commit failed!  Quitting."
        echo "***********************************************************************"
        exit 1
    fi
fi

git -C $pagespath push origin ghpages
push_retval=$?
if [[ "$push_retval" != 0 ]]; then
    echo "***********************************************************************"
    echo "ERROR: git push failed!  Quitting."
    echo "***********************************************************************"
    exit 1
fi

echo "SUCCESS: Completed $reponame deploy_pages.sh without error"
exit 0
