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

"""Utilities for tracking and monitoring memory and resource usage."""
import logging
import socket

import resource

LOG = logging.getLogger(__name__)


try:
    import psutil
except ImportError:
    LOG.info(
        "Failed import psutil in utils/memusg.py. " + "If you need it, install it."
    )


def print_mem_usage(logstr="", verbose=False):
    """Print memory usage to LOG.info.

    * By default include psutil output.
    * If verbose is True, include output from both psutil and resource packages.
    """
    # If psutil / socket / resource are not imported, do not fail
    usage_dict = {}
    try:
        vmem_percent = psutil.virtual_memory().percent
        LOG.info(
            "virtual perc: %s on %s %s",
            str(vmem_percent),
            str(socket.gethostname()),
            logstr,
        )
        swap_percent = psutil.swap_memory().percent
        LOG.info(
            "swap perc:    %s on %s %s",
            str(swap_percent),
            str(socket.gethostname()),
            logstr,
        )
    except NameError as resp:
        vmem_percent = swap_percent = "nan"
        LOG.info(
            "%s: psutil or socket not defined, no percent memusg output", str(resp)
        )
    try:
        highest = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        LOG.info(
            "highest:      %s on %s %s",
            str(highest),
            str(socket.gethostname()),
            logstr,
        )
    except NameError as resp:
        highest = "nan"
        LOG.info(
            "%s: resource or socket not defined, no highest memusg output", str(resp)
        )

    if verbose:
        usage_dict = print_resource_usage(logstr)
    usage_dict["memusg_virtual"] = vmem_percent
    usage_dict["memusg_swap"] = swap_percent
    usage_dict["memusg_highest"] = highest
    return usage_dict


def print_resource_usage(logstr=""):
    """Print verbose resource usage, using "resource" package."""
    usage_dict = {}
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        for name, desc in [
            ("ru_utime", "RESOURCE " + logstr + " User time"),
            ("ru_stime", "RESOURCE " + logstr + " System time"),
            ("ru_maxrss", "RESOURCE " + logstr + " Max. Resident Set Size"),
            ("ru_ixrss", "RESOURCE " + logstr + " Shared Memory Size"),
            ("ru_idrss", "RESOURCE " + logstr + " Unshared Memory Size"),
            ("ru_isrss", "RESOURCE " + logstr + " Stack Size"),
            ("ru_inblock", "RESOURCE " + logstr + " Block inputs"),
            ("ru_oublock", "RESOURCE " + logstr + " Block outputs"),
        ]:
            LOG.info("%-25s (%-10s) = %s", desc, name, getattr(usage, name))
            usage_dict[name] = getattr(usage, name)
    except NameError:
        LOG.info("resource not defined")
    return usage_dict
