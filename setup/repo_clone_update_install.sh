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

# These commands loop through all required plugins and test data repos for a given package.

# internal_plugins, internal_algs, external_repos, and test_repos set within <package> setup_<package>.sh

if [[ "$1" == "setup" ]]; then
    if [[ -z "$GEOIPS_PACKAGES_DIR" ]]; then
        echo "Must define GEOIPS_PACKAGES_DIR environment variable prior to setting up geoips"
        exit 1
    fi
    if [[ -z "$GEOIPS_REPO_URL" && -z "$GEOIPS_BASE_URL" ]]; then
        echo "Must defined GEOIPS_REPO_URL environment variable prior to setting up geoips"
        exit 1
    fi

    if [[ -z $GEOIPS_DEPENDENCIES_DIR ]]; then
        export GEOIPS_DEPENDENCIES_DIR=$GEOIPS_PACKAGES_DIR/../geoips_dependencies
    fi
    if [[ -z $GEOIPS_TESTDATA_DIR ]]; then
        export GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/../test_data
    fi
    if [[ -z $BASECONDAPATH ]]; then
        export BASECONDAPATH=$GEOIPS_DEPENDENCIES_DIR/miniconda3/bin
    fi
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/bin
    mkdir -p $GEOIPS_PACKAGES_DIR
    mkdir -p $GEOIPS_TESTDATA_DIR

    source $GEOIPS_PACKAGES_DIR/geoips/setup/geoips_conda_init_setup

elif [[ "$1" == "repo_clone" ]]; then
    for internal_repo in $internal_plugins $internal_algs; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_source_repo $internal_repo
        retval=$?
        if [[ $retval != 0 ]]; then
            echo "******FAILED repo_clone internal repos - please resolve and rerun repo_clone command"
            exit 1
        fi
    done
    for external_repo in $external_repos; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_external_repo $external_repo
        retval=$?
        if [[ $retval != 0 ]]; then
            echo "******FAILED repo_clone external repos - please resolve and rerun repo_clone command"
            exit 1
        fi
    done
    for test_repo in $test_repos; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_test_repo $test_repo
        retval=$?
        if [[ $retval != 0 ]]; then
            echo "******FAILED repo_clone test repo - please resolve and rerun repo_clone command"
            exit 1
        fi
    done

elif [[ "$1" == "repo_update" ]]; then
    if [[ "$2" == "" ]]; then
        branch=dev
    else
        branch=$2
    fi
    if [[ "$3" == "" ]]; then
        do_not_fail=""
    else
        do_not_fail="do_not_fail"
    fi
    for internal_plugin in $internal_plugins; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_source_repo $internal_plugin $branch $do_not_fail
        retval=$?
        if [[ $retval != 0 && "$do_not_fail" != "do_not_fail" ]]; then
            echo "******FAILED repo_update internal plugin - please resolve and rerun repo_update command"
            exit 1
        fi
    done
    for internal_alg in $internal_algs; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_source_repo $internal_alg $branch $do_not_fail
        retval=$?
        if [[ $retval != 0 && "$do_not_fail" != "do_not_fail" ]]; then
            echo "******FAILED repo_update internal alg - please resolve and rerun repo_update command"
            exit 1
        fi
    done
    for external_repo in $external_repos; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_external_repo $external_repo $do_not_fail
        retval=$?
        if [[ $retval != 0 && "$do_not_fail" != "do_not_fail" ]]; then
            echo "******FAILED repo_update external repo - please resolve and rerun repo_update command"
            exit 1
        fi
    done
    for test_repo in $test_repos; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_test_repo $test_repo $branch $do_not_fail
        retval=$?
        if [[ $retval != 0 && "$do_not_fail" != "do_not_fail" ]]; then
            echo "******FAILED repo_update test repo - please resolve and rerun repo_update command"
            exit 1
        fi
    done

elif [[ "$1" == "install_plugins" ]]; then

    installed_plugins_path=$GEOIPS_PACKAGES_DIR/installed_geoips_plugins.txt

    for plugin in $internal_plugins $internal_algs $external_repos; do
        echo ""
        echo "Trying plugin '$plugin', checking $installed_plugins_path"
        found="false"
        if [[ -f $installed_plugins_path ]]; then
            while read installed_plugin; do
                if [[ "$installed_plugin" == "$plugin" ]]; then
                    found="true"
                fi
            done < $installed_plugins_path
            if [[ "$found" == "true" ]]; then
                echo "Plugin $plugin already installed, skipping"
                continue
            fi
        fi
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh install_plugin $plugin
        retval=$?
        if [[ $retval != 0 ]]; then
            echo "******FAILED install_plugins - please resolve and rerun install_plugins command"
            exit 1
        fi
    done

elif [[ "$1" == "uncompress_test_data" ]]; then
    for test_repo in $test_repos; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh uncompress_test_data $test_repo
    done
    for internal_plugin in $internal_plugins; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh uncompress_test_data $internal_plugin
    done

elif [[ "$1" == "recompress_test_data" ]]; then
    for test_repo in $test_repos; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh recompress_test_data $test_repo
    done
    for internal_plugin in $internal_plugins; do
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh recompress_test_data $internal_plugin
    done

fi
