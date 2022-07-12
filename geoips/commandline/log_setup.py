# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

def setup_logging(verbose=True):
    import logging
    import sys
    # If you do this the first time with no argument, it sets up the logging for all submodules
    # subsequently, in submodules, you can just do LOG = logging.getLogger(__name__)
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(module)12s%(lineno)4d%(levelname)7s: %(message)s',
                            '%d_%H%M%S')
    if not verbose:
        fmt = logging.Formatter('%(asctime)s: %(message)s',
                                '%d_%H%M%S')
    stream_hndlr = logging.StreamHandler(sys.stdout)
    stream_hndlr.setFormatter(fmt)
    stream_hndlr.setLevel(logging.INFO)
    log.addHandler(stream_hndlr)
    return log

