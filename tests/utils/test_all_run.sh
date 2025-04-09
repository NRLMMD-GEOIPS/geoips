# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

    # Set a unique log file for the current script - this allows us to check output from individual calls.
    script_path=`echo $call | cut -d " " -f1`
    script_args=`echo $call | cut -d " " -f2-`
    # If there are no arguments, script_args will just be the path
    if [[ "$script_args" == "$script_path" ]]; then
        script_args=""
    else
        script_args=_${script_args// /_}
        script_args=_${script_args//\//_}
    fi
    script_name=`basename $script_path`
    script_log=${LOGFILE}_${script_name}${script_args}.log

    echo `date` " Running $script_name"
    echo $call

    overall_num=$((overall_num+1))
    curr_start=`date +%s`

    echo $script_log
    $call >> $script_log 2>&1
    overall_procflow_retvals[$overall_num]=$?

    curr_end=`date +%s`
    overall_calls[$overall_num]="$call"
    overall_runtimes[$overall_num]=$((curr_end-curr_start))

    echo "" >> $LOGFILE 2>&1
    echo "" >> $LOGFILE 2>&1
    echo "$script_log" >> $LOGFILE 2>&1
    echo "" >> $LOGFILE 2>&1

    # Just log this, do not use for return value
    grep "Number outputs expected" $script_log >> $LOGFILE 2>&1
    grep "BADCOMPARE " $script_log >> $LOGFILE 2>&1
    bad_compare_retval=$?
    grep "MISSINGCOMPARE " $script_log >> $LOGFILE 2>&1
    missing_compare_retval=$?
    grep "MISSINGPRODUCT" $script_log >> $LOGFILE 2>&1
    missing_product_retval=$?
    grep "FAILED INTERFACE" $script_log >> $LOGFILE 2>&1
    failed_interface_retval=$?
    grep "DATABASEFAILURE" $script_log >> $LOGFILE 2>&1
    database_failed_retval=$?
    # Just log this, do not use for return value
    grep "Error" $script_log >> $LOGFILE 2>&1


    grep "SUCCESSFUL COMPARISON DIR:" $script_log >> $LOGFILE 2>&1
    config_retval=$?
    grep "GOODCOMPARE " $script_log >> $LOGFILE 2>&1
    product_compare_retval=$?
    grep "FOUNDPRODUCT" $script_log >> $LOGFILE 2>&1
    cylc_test_retval=$?
    grep "SETUPSUCCESS" $script_log >> $LOGFILE 2>&1
    cylc_setup_retval=$?
    grep "SUCCESSFUL INTERFACE" $script_log >> $LOGFILE 2>&1
    success_interface_retval=$?
    grep "DATABASESUCCESS" $script_log >> $LOGFILE 2>&1
    database_success_retval=$?
    
    if [[ $overall_procflow_retvals[$overall_num] == 0 && $config_retval != 0 && $product_compare_retval != 0 && $cylc_test_retval != 0 && $cylc_setup_retval != 0 && $success_interface_retval != 0 && $database_success_retval != 0 ]]; then
        echo "  FAILED Log output did not contain SUCCESSFUL COMPARISON DIR, GOODCOMPARE, FOUNDPRODUCT, SETUPSUCCESS, SUCCESSFUL INTERFACE, or DATABASESUCCESS"
        echo "      False 0 return?"
        echo "      Please check test script to ensure output is set properly,"
        echo "      and ensure log output includes valid success strings"
        echo "  FAILED Log output did not contain SUCCESSFUL COMPARISON DIR, GOODCOMPARE, FOUNDPRODUCT, SETUPSUCCESS, SUCCESSFUL INTERFACE, or DATABASESUCCESS" >> $LOGFILE 2>&1
        echo "      False 0 return?" >> $LOGFILE 2>&1
        echo "      Please check test script to ensure output is set properly," >> $LOGFILE 2>&1
        echo "      and ensure log output includes valid success strings" >> $LOGFILE 2>&1
        overall_procflow_retvals[$overall_num]=42
    fi
    if [[ $overall_procflow_retvals[$overall_num] == 0 && ( $bad_compare_retval == 0 || $missing_compare_retval == 0 || $missing_product_retval == 0 || $failed_interface_retval == 0 || $database_failed_retval == 0 ) ]]; then
        echo "  FAILED Log output DID contain BADCOMPARE, MISSINGCOMPARE, MISSINGPRODUCT, FAILED INTERFACE, or DATABASEFAILURE"
        echo "      False 0 return?"
        echo "      Please check test script to ensure output is set properly,"
        echo "      and ensure log output includes valid success strings"
        echo "  FAILED Log output DID contain BADCOMPARE, MISSINGCOMPARE, MISSINGPRODUCT, FAILED INTERFACE, or DATABASEFAILURE" >> $LOGFILE 2>&1
        echo "      False 0 return?" >> $LOGFILE 2>&1
        echo "      Please check test script to ensure output is set properly," >> $LOGFILE 2>&1
        echo "      and ensure log output includes valid success strings" >> $LOGFILE 2>&1
        overall_procflow_retvals[$overall_num]=42
    fi

    echo "        Return: ${overall_procflow_retvals[*]: -1}"
    echo ""
