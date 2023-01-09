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

''' Utilities for tracking and monitoring memory and resourc usage '''

import logging
import socket

import resource
try:
    import psutil
except ImportError:
    print('Failed import psutil in utils/memusg.py. ' +
          'If you need it, install it.')

LOG = logging.getLogger(__name__)


def print_mem_usage(logstr='', verbose=False):
    # If psutil / socket / resource are not imported, do not fail
    try:
        LOG.info('virtual perc: %s on %s %s',
                 str(psutil.virtual_memory().percent),
                 str(socket.gethostname()),
                 logstr)
        LOG.info('swap perc:    %s on %s %s',
                 str(psutil.swap_memory().percent),
                 str(socket.gethostname()),
                 logstr)
    except NameError as resp:
        LOG.info('%s: psutil or socket not defined, no percent memusg output', str(resp))
    try:
        LOG.info('highest:      %s on %s %s',
                 str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                 str(socket.gethostname()),
                 logstr)
    except NameError as resp:
        LOG.info('%s: resource or socket not defined, no highest memusg output', str(resp))
    if verbose:
        print_resource_usage(logstr)


def print_resource_usage(logstr=''):
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        for name, desc in [
               ('ru_utime', 'RESOURCE '+logstr+' User time'),
               ('ru_stime', 'RESOURCE '+logstr+' System time'),
               ('ru_maxrss', 'RESOURCE '+logstr+' Max. Resident Set Size'),
               ('ru_ixrss', 'RESOURCE '+logstr+' Shared Memory Size'),
               ('ru_idrss', 'RESOURCE '+logstr+' Unshared Memory Size'),
               ('ru_isrss', 'RESOURCE '+logstr+' Stack Size'),
               ('ru_inblock', 'RESOURCE '+logstr+' Block inputs'),
               ('ru_oublock', 'RESOURCE '+logstr+' Block outputs'),
               ]:
            LOG.info('%-25s (%-10s) = %s', desc, name, getattr(usage, name))
    except NameError:
        LOG.info('resource not defined')
