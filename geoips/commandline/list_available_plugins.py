# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Simple script to list available plugins for each interface."""

import warnings
import os.path
from geoips.interfaces.base import BaseInterface
from geoips import interfaces
from geoips.filenames.base_paths import PATHS as gpaths
from geoips.commandline.log_setup import setup_logging
from geoips.commandline.args import get_argparser, check_command_line_args

# Always actually raise DeprecationWarnings
# Note this SO answer https://stackoverflow.com/a/20960427
warnings.simplefilter("always", DeprecationWarning)


def main():
    """Script to list all modules available in the current geoips instantiation."""
    supported_args = ["logging_level"]

    # Use standard GeoIPS argparser - use standard formatting for standard args.
    parser = get_argparser(
        arglist=supported_args,
        description="List available plugins within the current geoips instantiation.",
    )
    # Add our specific "interfaces" argument.
    parser.add_argument(
        "interfaces",
        nargs="*",
        default=None,
        help="""List of interfaces to include.  If None, include all interfaces.""",
    )
    # Add "package_name" argument.
    parser.add_argument(
        "--package_name",
        "-p",
        default=None,
        help="""Package to run.  If None, include all packages.""",
    )
    # Add "repo_path" argument.
    parser.add_argument(
        "--repo_path",
        "-r",
        default=None,
        help="""Path to package to run.  If None, use GEOIPS_PACKAGES_DIR/pkgname.""",
    )

    # Get the dictionary of command line args.
    COMMAND_LINE_ARGS = parser.parse_args().__dict__
    # Check included arguments for appropriate formatting / type.
    check_command_line_args(supported_args, COMMAND_LINE_ARGS)
    package_name = COMMAND_LINE_ARGS["package_name"]
    repo_path = COMMAND_LINE_ARGS["repo_path"]
    if package_name and not repo_path:
        repo_path = f"{gpaths['GEOIPS_PACKAGES_DIR']}/{package_name}"

    if repo_path and not os.path.isdir(repo_path):
        raise IOError(f"FAILED Specified repo path {repo_path} does not exist")

    # Setup logging at the requested logging level.
    LOG = setup_logging(logging_level=COMMAND_LINE_ARGS["logging_level"])
    if package_name:
        LOG.interactive(
            f"ONLY RUNNING package_name {package_name} repo_path {repo_path}"
        )
    else:
        LOG.interactive("RUNNING ALL plugin repos")
    if COMMAND_LINE_ARGS["interfaces"]:
        LOG.interactive(f"ONLY RUNNING interfaces {COMMAND_LINE_ARGS['interfaces']}")
    else:
        LOG.interactive("RUNNING ALL interfaces")

    # If "interfaces" is not specified command line or all interfaces are requested,
    # then include plugins for all interfaces.
    if not COMMAND_LINE_ARGS["interfaces"] or COMMAND_LINE_ARGS["interfaces"] == [
        "all"
    ]:
        curr_interfaces = interfaces.__dict__.values()
    else:
        curr_interfaces = [
            interfaces.__dict__[curr_interface]
            for curr_interface in COMMAND_LINE_ARGS["interfaces"]
        ]

    # Print just the interface name and plugin name for each plugin in each
    # requested interface.
    # Additionally, filter all valid interfaces out first. For some reason,
    # 'curr_interfaces' size would change over the full loop (if concatenated) with the
    # loop below, and testing would always fail. I could not locate where and why the
    # change in size occured. There is no code that directly modifies 'curr_interfaces',
    # but filtering out beforehand works. This also occurs in
    # geoips/tests/utils/test_interfaces.py as well. This is a really weird bug.
    val_interfaces = []
    for curr_interface in curr_interfaces:
        # Do not test anything that is not a valid GeoIPS interface; there are lots of
        # weird values in interfaces.__dict__ that don't relate to the testing set here
        # at all. Like this:

        # '{open': <function io.open(file, mode='r', buffering=-1, encoding=None,
        # errors=None, newline=None, closefd=True, opener=None)>,
        # 'copyright': Copyright (c) 2001-2023 Python Software Foundation.
        # All Rights Reserved...'}
        if (type(curr_interface) is BaseInterface) or not isinstance(
            curr_interface, BaseInterface
        ):
            continue
        val_interfaces.append(curr_interface)

    for curr_interface in val_interfaces:
        if curr_interface.name == "workflows":
            # Don't test workflows right now; they differ from other plugin objects
            # currently
            continue
        # This prints a "horizontal line" character U+2015, not a dash
        LOG.interactive("―" * len(curr_interface.name))
        LOG.interactive(f"{curr_interface.name}")
        LOG.interactive("―" * len(curr_interface.name))
        plugin_names = []
        for plg in curr_interface.get_plugins():
            if package_name and hasattr(plg, "package") and plg.package == package_name:
                plugin_names += [plg.name]
            if repo_path and hasattr(plg, "module") and repo_path in str(plg.module):
                plugin_names += [plg.name]
            if not package_name and not repo_path:
                plugin_names += [plg.name]
        LOG.interactive(", ".join(sorted(plugin_names)))


if __name__ == "__main__":
    main()
