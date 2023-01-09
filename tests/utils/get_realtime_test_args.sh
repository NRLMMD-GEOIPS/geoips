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

if [[ "$1" != "write_output_file_list" && "$1" != "copy_files" && "$1" != "run_file_list_comparison" ]]; then
    echo "Usage: $0 <output_file_arg> [<copy_base_dir>]"
    echo "    Where <output_file_arg> one of:"
    echo "      write_output_file_list"
    echo "      copy_files"
    echo "      run_file_list_comparison"
    echo ""
    echo "ie: create a new output file list based on current run:"
    echo "    $0 write_output_file_list"
    echo ""
    echo "ie: copy the files contained in the output file list to directory <copy_dir>:"
    echo "    $0 copy_files <copy_base_dir>"
    echo ""
    echo "ie: run the test and compare to the output file list $expected_outputs:"
    echo "    $0 run_file_list_comparison"
    echo ""
    exit 1
fi

# Identify list of expected output products:
expected_outputs=$GEOIPS_SYSTEM/tests/realtime_tests/output_file_lists/$source_name.txt

output_file_list_fname_arg=""
if [[ "$1" == "write_output_file_list" ]]; then
    output_file_list_fname_arg="--output_file_list_fname $expected_outputs"
fi

copy_dir=""
if [[ "$1" == "copy_files" && "$2" != "" && -d "$2" ]]; then
    copy_base_dir=$2
    copy_dir="$copy_base_dir/$source_name"
    mkdir -p $copy_dir
    echo "NOTE: Will copy output files to $copy_dir"
fi
