.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Using ``inotifywait`` for Near Real-Time Processing
===================================================

This tutorial explains how to set up a simple script to run **GeoIPS** for near
real-time data processing using ``inotifywait``. This is a simple exmaple that
can be extended by the user to fit their needs.  For more complex workflows,
consider:

- extending this example
- rewriting this example in Python using its ``inotify`` or ``watchdog`` packages
- using dedicated tools like cron jobs, task schedulers, or more advanced
  monitoring setups

Potential Shortcomings
----------------------

1. **No Support for Remote Filesystems**: This script uses ``inotify`` which
   does not support remote filesystems.  If your data is on a remote
   filesystem, you will need to use a different solution such as fswatch, a
   cron job, or a custom Python script.
2. **Single File Processing**: This script processes files one by one.
   There is no multi-processing. More complex logic could be added to handle
   situations that require multiple data files for each call to GeoIPS or that
   require additional filtering of files.
3. **No Error Handling**: If GeoIPS fails to process a file,
   the script does not handle errors or retries. These can be handled through
   use of ``$?`` which will contain the exit code. If non-zero, GeoIPS
   encountered an error while processing.
4. **File Completion Assumption**: The script assumes the file is complete when
   the ``close_write`` event occurs, but there is a chance of partial files if
   they're moved or copied slowly (eg. copying over a network connection).

Step 1: Install Dependencies
----------------------------

``inotifywait`` is a tool that watches for new files in a directory. We will
use ``inotifywait`` to watch for files and call GeoIPS each time one appears.
Make sure you have ``inotifywait``
<https://github.com/inotify-tools/inotify-tools/tree/master>_ installed.

On Debian machines, you can install it with:

.. code-block:: bash

    sudo apt-get install inotify-tools

On Red-Hat machines, you can install it with:

.. code-block:: bash

    sudo dnf install inotify-tools

Step 2: Create a Watch Script
-----------------------------

Create a shell script that will monitor a directory and process new files using GeoIPS.
This is an example script, but you can run whatever processing you want:

.. code-block:: bash

    #!/bin/bash

    WATCH_DIR="/path/to/watch/directory"  # Directory to watch for new files
    mkdir -p $WATCH_DIR # Make directory if it doesn't exist

    # Run inotifywait in a loop to monitor for new files
    inotifywait -m -e close_write --format "%f" "$WATCH_DIR" | while read FILENAME
    do
        echo "Processing new file: $FILENAME"
        geoips run single_source \
             --reader_name abi_netcdf \
             --product_name Visible \
             --output_formatter unprojected_image \
             --filename_formatter geoips_fname \
             --self_register_dataset MED \
             --self_register_source abi \
             "$WATCH_DIR/$FILENAME"
    done

Save this script as ``geoips-watch.sh`` and give it execute permissions:

.. code-block:: bash

    chmod +x geoips-watch.sh

Step 3: Run the Watch Script
----------------------------

Start the script to begin monitoring the directory for new files:

.. code-block:: bash

    ./geoips-watch.sh

The script triggers a GeoIPS run when a new file is written.

To run in the background and capture logs, use:

.. code-block:: bash

    nohup ./geoips-watch.sh > geoips-watch.log 2>&1 &
