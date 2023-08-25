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

"""Command line script for kicking off geoips based procflows.

MUST call with --procflow.
"""

from datetime import datetime
from geoips.commandline.log_setup import setup_logging
from geoips.commandline.args import get_command_line_args
from geoips.interfaces import procflows


def main(get_command_line_args_func=None):
    """Script to kick off processing based on command line args.

    Parameters
    ----------
    get_command_line_args_func : function, optional
        Function to use in place of "get_command_line_args", default None
        If None, use geoips.commandline.args.get_command_line_args
    """
    DATETIMES = {}
    DATETIMES["start"] = datetime.utcnow()

    if get_command_line_args_func is None:
        get_command_line_args_func = get_command_line_args
    # arglist=None allows all possible arguments.
    ARGS = get_command_line_args_func(
        arglist=None, description="Run data file processing"
    )

    COMMAND_LINE_ARGS = ARGS.__dict__
    if "logging_level" in COMMAND_LINE_ARGS.keys():
        LOG = setup_logging(logging_level=COMMAND_LINE_ARGS["logging_level"])
    else:
        LOG = setup_logging()
    LOG.info("RETRIEVED COMMAND LINE ARGUMENTS")
    LOG.interactive("\n\n\nStarting %s procflow...\n\n", COMMAND_LINE_ARGS["procflow"])
    import sys

    LOG.info(
        "COMMANDLINE CALL: \n    %s",
        "\n        ".join([currarg + " \\" for currarg in sys.argv]),
    )

    # LOG.info(COMMAND_LINE_ARGS)
    LOG.info("GETTING PROCFLOW MODULE")
    PROCFLOW = procflows.get_plugin(COMMAND_LINE_ARGS["procflow"])

    LOG.info(f"CALLING PROCFLOW MODULE: {PROCFLOW.name}")
    if PROCFLOW:
        LOG.info(COMMAND_LINE_ARGS["filenames"])
        LOG.interactive(
            "\n\n\nRunning on filenames: %s\n\n", COMMAND_LINE_ARGS["filenames"]
        )
        LOG.info(COMMAND_LINE_ARGS)
        LOG.info(PROCFLOW)
        RETVAL = PROCFLOW(COMMAND_LINE_ARGS["filenames"], COMMAND_LINE_ARGS)
        LOG.interactive(
            "Completed geoips PROCFLOW %s processing, done!",
            COMMAND_LINE_ARGS["procflow"],
        )
        LOG.info("Starting time: %s", DATETIMES["start"])
        LOG.info("Ending time: %s", datetime.utcnow())
        LOG.interactive("Total time: %s", datetime.utcnow() - DATETIMES["start"])
        if isinstance(RETVAL, list):
            for ret in RETVAL:
                LOG.interactive("GEOIPSPROCFLOWSUCCESS %s", ret)
            if len(RETVAL) > 2:
                LOG.interactive(
                    "GEOIPSTOTALSUCCESS %s %s products generated, total time %s",
                    str(PROCFLOW.name),
                    len(RETVAL),
                    datetime.utcnow() - DATETIMES["start"],
                )
            else:
                LOG.interactive(
                    "GEOIPSNOSUCCESS %s %s products generated, total time %s",
                    str(PROCFLOW.name),
                    len(RETVAL),
                    datetime.utcnow() - DATETIMES["start"],
                )
            sys.exit(0)
        # LOG.info('Return value: %s', bin(RETVAL))
        LOG.interactive("Return value: %d", RETVAL)
        sys.exit(RETVAL)

    else:
        raise IOError(
            "FAILED no geoips*/{0}.py with def {0}".format(
                COMMAND_LINE_ARGS["procflow"]
            )
        )


if __name__ == "__main__":
    main()
