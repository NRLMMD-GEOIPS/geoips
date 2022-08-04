if [[ "$1" == "gitlfs" ]]; then
    git lfs install
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'git lfs install' failed, please install git lfs before proceeding"
    else
        echo ""
        echo "SUCCESS: 'git lfs install' appears to be installed successfully"
    fi 
fi

if [[ "$1" == "imagemagick" ]]; then
    compare --version
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'compare --version' failed, please install imagemagick before proceeding"
    else
        echo ""
        echo "SUCCESS: imagemagick 'compare --version' appears to be installed successfully"
    fi
fi

if [[ "$1" == "wget" ]]; then
    wget --version
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'wget --version' failed, please install wget before proceeding"
    else
        echo ""
        echo "SUCCESS: 'wget --version' appears to be installed successfully"
    fi
fi

if [[ "$1" == "git" ]]; then
    git --help
    echo ""
    git --version
    echo ""
    echo "NOTE: ensure git version is >= 2.0, and git --help includes '-C' option"
fi