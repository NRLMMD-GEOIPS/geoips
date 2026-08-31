# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh
# Deploy Sphinx doc to GitHub Pages
echo "***"
echo "Requires docs/build_docs.sh run first"
echo "Will create/update/push ghpages branch"
echo "***"

echo "geoips_repo_url $geoips_repo_url"
echo "GEOIPS_PACKAGES_DIR $GEOIPS_PACKAGES_DIR"

if [[ "$1" == "" || "$2" == "" || "$3" == "" || "$4" == "" ]]; then
    echo "***************************************************************************"
    failed="true"
fi
if [[ ! -d "$1" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Passed repository path does not exist."
    echo "       $1"
    failed="true"
fi

# Expected that build_docs.sh has already been run.
# Keep documentation build and deploy separate steps.
repopath=`realpath $1`
if [[ ! -d "$repopath" ]]; then
    echo "***************************************************************************"
    echo "ERROR: Repository 'realpath' does not exist:"
    echo "       $repopath"
    failed="true"
fi

if [[ "$failed" == "true" ]]; then
    echo "ERROR: Must call with repo path and geoips_repo_url and pages path.  Ie"
    echo "    $0 $GEOIPS_PACKAGES_DIR/geoips https://github.com/NRLMMD-GEOIPS ./ghpages_geoips geoips"
    echo "    $0 $GEOIPS_PACKAGES_DIR/data_fusion https://github.com/NRLMMD-GEOIPS ./ghpages_data_fusion data_fusion"
    echo "    $0 $GEOIPS_PACKAGES_DIR/template_basic_plugin https://github.com/NRLMMD-GEOIPS ./ghpages_template_basic_plugin template_basic_plugin"
    echo "***************************************************************************"
    exit 1
fi
geoips_repo_url=$2
docpath=$repopath/docs/build/sphinx/html

echo "docpath=$docpath"

if [[ ! -d $docpath ]]; then
    echo ""
    echo "***************************************************************************"
    echo "ERROR: Pre-built html documentation does not exist."
    echo "Ensure you successfully run build_docs.sh prior to deploy_pages.sh"
    echo ""
    echo "  $GEOIPS_PACKAGES_DIR/geoips/build_docs.sh $1 <package_name>"
    echo "  $GEOIPS_PACKAGES_DIR/geoips/deploy_pages.sh $1 $2"
    echo "***************************************************************************"
    echo ""
    exit 1
fi

pagespath=`realpath $3`
reponame="$4"

if [[ -d $pagespath ]]; then
    echo "***********************************************************************"
    echo "ERROR: $pagespath already exists.  Remove and try again."
    echo "***********************************************************************"
    exit 1
fi

if [[ ! -d $pagespath ]]; then
    mkdir -p $pagespath
    echo "***"
    echo "Cloning $reponame repo"
    echo "git clone $geoips_repo_url/$reponame $pagespath/ghpages_repo_clone"
    echo "***"
    git clone $geoips_repo_url/$reponame $pagespath/ghpages_repo_clone
    clone_retval=$?
    if [[ "$clone_retval" != "0" ]]; then
        echo "***********************************************************************"
        echo "ERROR: git clone failed!  Quitting."
        echo "***********************************************************************"
        exit 1
    fi
fi

if [[ ! -d $pagespath/ghpages_repo_clone ]]; then
    echo "***************************************************************************"
    echo "ERROR: ghpages directory was not successfully created!  Quitting."
    echo "***************************************************************************"
    exit 1
fi

echo "***"
echo "Update to ghpages branch"
echo "git -C $pagespath/ghpages_repo_clone fetch --all -p"
echo "git -C $pagespath/ghpages_repo_clone checkout ghpages"
echo "git -C $pagespath/ghpages_repo_clone pull"
echo "***"

git -C $pagespath/ghpages_repo_clone fetch --all -p

git -C $pagespath/ghpages_repo_clone checkout ghpages
checkout_retval=$?
if [[ "$checkout_retval" != 0 ]]; then
    echo "***********************************************************************"
    echo "ERROR: git checkout failed!  Quitting."
    echo "***********************************************************************"
    exit 1
fi

git -C $pagespath/ghpages_repo_clone pull
pull_retval=$?
if [[ "$pull_retval" != 0 ]]; then
    echo "***********************************************************************"
    echo "ERROR: git pull failed!  Quitting."
    echo "***********************************************************************"
    exit 1
fi

echo "***"
echo "remove previously generated to clear discontinued modules"
echo "rm -rf $pagespath/ghpages_repo_clone/docs/*"
echo "cp -R $docpath/*"
echo "      $pagespath/ghpages_repo_clone/docs"
echo "***"
rm -rf $pagespath/ghpages_repo_clone/docs/*
if [[ ! -d $pagespath/ghpages_repo_clone/docs ]]; then
    echo "***"
    echo "mkdir $pagespath/ghpages_repo_clone/docs"
    mkdir $pagespath/ghpages_repo_clone/docs
    echo "***"
fi
cp -R $docpath/* $pagespath/ghpages_repo_clone/docs
if [[ ! -f $pagespath/ghpages_repo_clone/docs/.nojekyll ]]; then
    # .nojekyll ensures github pages does not attempt to use jekyll themes for
    # rendering the html.  This file should already exist in the docs directory
    # (and not be deleted with the rm -rf docs/* above, since it is hidden), but
    # touch included here for insurance.  When .nojekyll does not exist, no
    # style information is available (since jekyll ignores _* directories),
    # so the html rendering is very ugly.
    echo "***"
    echo "Ensure .nojekyll file exists for proper github pages rendering"
    echo "touch $pagespath/ghpages_repo_clone/docs/.nojekyll"
    touch $pagespath/ghpages_repo_clone/docs/.nojekyll
    echo "***"
fi

echo "***"
echo "Adding new/updated files"
echo "git -C $pagespath/ghpages_repo_clone add docs"
echo "git -C $pagespath/ghpages_repo_clone status"
echo "***"
git -C $pagespath/ghpages_repo_clone add docs
git -C $pagespath/ghpages_repo_clone status

echo "***"
echo "Set git status for obtaining current branch"
echo "gstatus=(\`git -C $repopath status\`)"
gstatus=(`git -C $repopath status`)
echo "$gstatus"
echo "***"

echo "***"
echo "Commit/push new/updated sphinx html files to ghpages branch"
echo "git -C $pagespath/ghpages_repo_clone commit -m 'sphinx html for github pages from: ${gstatus[2]}'"
echo "git -C $pagespath/ghpages_repo_clone push origin ghpages"
echo "***"

commit_output=`git -C $pagespath/ghpages_repo_clone commit -m "sphinx html for github pages from: ${gstatus[2]}"`
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

git -C $pagespath/ghpages_repo_clone push origin ghpages
push_retval=$?
if [[ "$push_retval" != 0 ]]; then
    echo "***********************************************************************"
    echo "ERROR: git push failed!  Quitting."
    echo "***********************************************************************"
    exit 1
fi

echo "SUCCESS: Completed $reponame deploy_pages.sh without error"
exit 0
