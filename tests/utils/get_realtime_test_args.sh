# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

if [[ "$1" != "write_output_file_list" && "$1" != *"copy_files" && "$1" != "run_file_list_comparison" && "$1" != "run_current" ]]; then
    echo "Usage: $0 <output_file_arg> [<copy_base_dir>]"
    echo "    Where <output_file_arg> one of:"
    echo "      write_output_file_list"
    echo "      write_output_file_list_and_copy_files"
    echo "      copy_files"
    echo "      run_file_list_comparison"
    echo "      run_file_list_comparison_and_copy_files"
    echo "      run_current"
    echo ""
    echo "ie: create a new output file list based on current run:"
    echo "    $0 write_output_file_list"
    echo ""
    echo "ie: create a new output file list based on current run, and copy files:"
    echo "    $0 write_output_file_list_and_copy_files <copy_base_dir>"
    echo ""
    echo "ie: copy the files contained in the output file list to directory <copy_dir>:"
    echo "    $0 copy_files <copy_base_dir>"
    echo ""
    echo "ie: run the test and compare to the output file list $expected_outputs:"
    echo "    $0 run_file_list_comparison"
    echo ""
    echo "ie: run the test and compare to the output file list $expected_outputs:"
    echo "    $0 run_file_list_comparison_and_copy_files <copy_base_dir>"
    echo ""
    exit 1
fi

# Identify list of expected output products:
expected_outputs=$GEOIPS_SYSTEM/tests/realtime_tests/output_file_lists/$source_name.txt

mkdir -p $GEOIPS_SYSTEM/tests/realtime_tests/output_file_lists_temp_current
expected_outputs_current=$GEOIPS_SYSTEM/tests/realtime_tests/output_file_lists_temp_current/$source_name.txt

output_file_list_fname_arg=""
if [[ "$1" == "write_output_file_list"* ]]; then
    if [[ ! -d $GEOIPS_SYSTEM/tests/realtime_tests/output_file_lists ]]; then
        echo "ERROR: $GEOIPS_SYSTEM/tests/realtime_tests/output_file_lists must exist to write_output_file_list! Quitting!"
        exit 1
    fi
    output_file_list_fname_arg="--output_file_list_fname $expected_outputs"
else
    output_file_list_fname_arg="--output_file_list_fname $expected_outputs_current"
fi

copy_dir=""
if [[ ( "$1" == *"copy_files" ) && "$2" != "" && -d "$2" ]]; then
    copy_base_dir=$2
    copy_dir="$copy_base_dir/$source_name"
    mkdir -p $copy_dir
    echo "NOTE: Will copy output files to $copy_dir"
elif [[ "$1" == "copy_files" && "$2" != "" && ! -d "$2" ]]; then
    echo "ERROR: $2 must exist to copy_files! Quitting!"
    exit 1
elif [[ "$1" == "copy_files" && "$2" == "" ]]; then
    echo "ERROR: $2 must be specified (and exist) to copy_files! Quitting!"
    exit 1
fi
