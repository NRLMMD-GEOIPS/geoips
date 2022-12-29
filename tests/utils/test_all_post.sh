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

echo ""
echo `date` " Running post, final results in $LOGFILE"


echo "" >> $LOGFILE 2>&1
echo "******Overall results from all test runs******" >> $LOGFILE 2>&1
echo "" >> $LOGFILE 2>&1

for curr_num in "${!overall_procflow_retvals[@]}"; do >> $LOGFILE 2>&1
    curr_return=${overall_procflow_retvals[$curr_num]} >> $LOGFILE 2>&1
    if [[ $curr_return > 1 ]]; then
        curr_return=1
    fi
    overall_procflow_retval=$((overall_procflow_retval+curr_return)) >> $LOGFILE 2>&1
    echo "" >> $LOGFILE 2>&1
    echo "${overall_calls[$curr_num]}" >> $LOGFILE 2>&1
    echo "Runtime: ${overall_runtimes[$curr_num]}" >> $LOGFILE 2>&1
    echo "return: $curr_return" >> $LOGFILE 2>&1
done >> $LOGFILE 2>&1

echo "" >> $LOGFILE 2>&1

overall_end=`date +%s` >> $LOGFILE 2>&1
overall_runtime=$((overall_end-overall_start)) >> $LOGFILE 2>&1

echo "" >> $LOGFILE 2>&1
echo "Package: $package_name" >> $LOGFILE 2>&1
echo "Total run time: $overall_runtime seconds" >> $LOGFILE 2>&1
echo "Number data types run: ${#overall_procflow_retvals[@]}" >> $LOGFILE 2>&1
echo "Number data types failed: $overall_procflow_retval" >> $LOGFILE 2>&1

echo ""
echo "Package: $package_name"
echo "Total run time: $overall_runtime seconds"
echo "Number data types run: ${#overall_procflow_retvals[@]}"
echo "Number data types failed: $overall_procflow_retval"

exit $overall_procflow_retval
