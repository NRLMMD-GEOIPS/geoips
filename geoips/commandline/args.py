# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Command line script for kicking off geoips based procflows."""

import argparse
import logging
from os.path import abspath, exists
from os import getenv
from geoips.filenames.base_paths import PATHS
from ast import literal_eval
import isodate

LOG = logging.getLogger(__name__)


def check_command_line_args(arglist, argdict):
    """Check formatting of command line arguments.

    Parameters
    ----------
    arglist : list of str
        List of desired command line arguments to check within argdict for
        appropriate formatting
    argdict : dict
        Dictionary of command line arguments

    Returns
    -------
    bool
        Return True if all arguments are of appropriate formatting.

    Raises
    ------
    TypeError
        Incorrect command line formatting
    """
    if arglist is None:
        return True
    if "filenames" in arglist:
        if argdict["filenames"] and not isinstance(argdict["filenames"], list):
            raise TypeError(
                'Must pass list of strings for "filenames" dictionary entry'
            )
        for fname in argdict["filenames"]:
            if not exists(fname):
                raise IOError(
                    f"Filename {fname} does not exist - all requested files must "
                    "exist on disk"
                )
        # LOG.info('COMMANDLINEARG filenames: %s', argdict['filenames'])
    if "self_register_dataset" in arglist:
        if argdict["self_register_dataset"] and not isinstance(
            argdict["self_register_dataset"], str
        ):
            raise TypeError(
                'Must pass string for "self_register_dataset" dictionary entry'
            )
        LOG.info(
            "COMMANDLINEARG self_register_dataset: %s", argdict["self_register_dataset"]
        )
    if "sectored_read" in arglist:
        if argdict["sectored_read"] and not isinstance(argdict["sectored_read"], bool):
            raise TypeError('Must pass bool for "sectored_read" dictionary entry')
        LOG.info("COMMANDLINEARG sectored_read: %s", argdict["sectored_read"])
    if "resampled_read" in arglist:
        if argdict["resampled_read"] and not isinstance(
            argdict["resampled_read"], bool
        ):
            raise TypeError('Must pass bool for "resampled_read" dictionary entry')
        LOG.info("COMMANDLINEARG resampled_read: %s", argdict["resampled_read"])
    if "sector_list" in arglist:
        if argdict["sector_list"] and not isinstance(argdict["sector_list"], list):
            raise TypeError(
                "Must pass list of strings for requested static sector plugins"
            )
        LOG.info("COMMANDLINEARG sector_list: %s", argdict["sector_list"])
    if "tcdb_sector_list" in arglist:
        if argdict["tcdb_sector_list"] and not isinstance(
            argdict["tcdb_sector_list"], list
        ):
            raise TypeError(
                'Must pass list of strings for "tcdb_sector_list" dictionary entry'
            )
        LOG.info("COMMANDLINEARG tcdb_sector_list: %s", argdict["tcdb_sector_list"])
    if "tcdb" in arglist:
        if argdict["tcdb"] not in [True, False]:
            raise TypeError("tcdb dictionary entry must be bool (True or False)")
        LOG.info("COMMANDLINEARG tcdb: %s", argdict["tcdb"])
    if "product_name" in arglist:
        if argdict["procflow"] == "single_source" and not argdict["product_name"]:
            raise TypeError(
                'Must pass a string for "product_name" when running "single_source"'
            )
        if argdict["product_name"] and not isinstance(argdict["product_name"], str):
            raise TypeError(
                'Must pass a single string for "product_name" dictionary entry'
            )
        LOG.info("COMMANDLINEARG product_name: %s", argdict["product_name"])
    if "product_options" in arglist:
        if argdict["product_options"] and not isinstance(
            argdict["product_options"], str
        ):
            raise TypeError('Must pass string for "product_options" dictionary entry')
        LOG.info("COMMANDLINEARG product_options: %s", argdict["product_options"])
    if "reader_name" in arglist:
        if argdict["reader_name"] and not isinstance(argdict["reader_name"], str):
            raise TypeError('Must pass string for "reader_name" dictionary entry')
        LOG.info("COMMANDLINEARG reader_name: %s", argdict["reader_name"])
    if "minimum_coverage" in arglist:
        if argdict["minimum_coverage"] and not isinstance(
            argdict["minimum_coverage"], float
        ):
            raise TypeError('Must pass float for "minimum_coverage" dictionary entry')
        LOG.info("COMMANDLINEARG minimum_coverage: %s", argdict["minimum_coverage"])
    if "output_config" in arglist:
        if argdict["output_config"] and not isinstance(argdict["output_config"], str):
            raise TypeError(
                'Must pass a single string for "output_config" dictionary entry'
            )
        LOG.info("COMMANDLINEARG output_config: %s", argdict["output_config"])
    if "output_file_list_fname" in arglist:
        if argdict["output_file_list_fname"] and not isinstance(
            argdict["output_file_list_fname"], str
        ):
            raise TypeError(
                "Must pass a single string for 'output_file_list_fname' dictionary "
                "entry"
            )
        LOG.info(
            "COMMANDLINEARG output_file_list_fname: %s",
            argdict["output_file_list_fname"],
        )
    if "sector_adjuster" in arglist:
        if argdict["sector_adjuster"] and not isinstance(
            argdict["sector_adjuster"], str
        ):
            raise TypeError(
                'Must pass a single string for "sector_adjuster" dictionary entry'
            )
        LOG.info("COMMANDLINEARG sector_adjuster: %s", argdict["sector_adjuster"])
    if "reader_defined_area_def" in arglist:
        if argdict["reader_defined_area_def"] and not isinstance(
            argdict["reader_defined_area_def"], bool
        ):
            raise TypeError(
                'Must pass True or False for "reader_defined_area_def" dictionary entry'
            )
        LOG.info(
            "COMMANDLINEARG reader_defined_area_def: %s",
            argdict["reader_defined_area_def"],
        )

    return True


def get_argparser(
    arglist=None, description=None, add_args_func=None, check_args_func=None
):
    """Get argparse.ArgumentParser with all standard arguments added.

    Parameters
    ----------
    arglist : list, optional
        list of requested arguments to add to the ArgumentParser, default None.
        if None, include all arguments
    description : str, optional
        String description of arguments, default None
    add_args_func : function, optional
        Alternative "add_args" function, default None
        If None, use internal "add_args"
    check_args_func: function, optional
        Alternative "check_args" function, default None
        If None, use internal "check_args"

    Returns
    -------
    argparse.ArgumentParser
        Including all requested/required command line arguments.
    """
    if add_args_func is None:
        add_args_func = add_args
    if check_args_func is None:
        check_args_func = check_command_line_args
    parser = argparse.ArgumentParser(description=description)
    add_args_func(parser, arglist)
    return parser


def get_command_line_args(
    arglist=None, description=None, add_args_func=None, check_args_func=None
):
    """Parse command line arguments specified by the requested list of arguments.

    Parameters
    ----------
    arglist : list, optional
        list of requested arguments to add to the ArgumentParser, default None.
        if None, include all arguments
    description : str, optional
        String description of arguments, default None
    add_args_func : function, optional
        Alternative "add_args" function, default None
        If None, use internal "add_args"
    check_args_func: function, optional
        Alternative "check_args" function, default None
        If None, use internal "check_args"

    Returns
    -------
    dict
        Dictionary of command line arguments
    """
    parser = get_argparser(arglist, description, add_args_func, check_args_func)
    argdict = parser.parse_args()
    if arglist and "filenames" in arglist and "procflow" in arglist:
        check_args_func(["filenames", "procflow"], argdict.__dict__)
    return argdict


def add_args(parser, arglist=None, legacy=False):
    """List of available standard arguments for calling data processing command line.

    Parameters
    ----------
    parser : ArgumentParser
        argparse ArgumentParser to add appropriate arguments
    arglist : list, optional
        list of requested arguments to add to the ArgumentParser, default None.
        if None, include all arguments
    legacy : bool, optional
        Represents whether or not a legacy 'run_procflow' or 'data_fusion_procflow'
        was called

    Returns
    -------
        No return values (parser modified in place)
    """
    if arglist is None or "filenames" in arglist:
        parser.add_argument(
            "filenames",
            nargs="*",
            default=None,
            type=abspath,
            help="""Fully qualified paths to data files to be processed.""",
        )

    if arglist is None or "outdir" in arglist:
        parser.add_argument(
            "-o",
            "--outdir",
            default=PATHS["GEOIPS_OUTDIRS"],
            help="""Path to write output files.  Defaults to GEOIPS_OUTDIRS.""",
        )

    if arglist is None or "logging_level" in arglist:
        parser.add_argument(
            "-l",
            "--logging_level",
            choices=["INTERACTIVE", "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"],
            default=None,
            help="""Specify logging config level for GeoIPS commands.""",
            type=str.upper,
        )
    if arglist is None or "rebuild_registries" in arglist:
        parser.add_argument(
            "--rebuild_registries",
            type=bool,
            choices=[True, False],
            # Will default to $GEOIPS_REBUILD_REGISTRIES if set, else True
            default=getenv("GEOIPS_REBUILD_REGISTRIES", True),
            help=(
                "Whether or not you want to rebuild plugin registries if you encounter "
                "a failure when retrieving a plugin."
            ),
        )

    sect_group = parser.add_argument_group(
        title="Sector Requests: General arguments for sectors"
    )
    if arglist is None or "sector_adjuster" in arglist:
        sect_group.add_argument(
            "--sector_adjuster",
            nargs="?",
            default=None,
            help="""Specify sector adjuster to be used within processing, located in:
                            <package>.plugins.modules.sector_adjusters.
                                <myadjuster>.<myadjuster>""",
        )
    if arglist is None or "sector_adjuster_kwargs" in arglist:
        sect_group.add_argument(
            "--sector_adjuster_kwargs",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify sector_adjuster kwargs that should be used for
                            this sector_adjuster. Should be formatted as a json
                            dictionary string""",
        )
    if arglist is None or "window_start_time" in arglist:
        sect_group.add_argument(
            "--window_start_time",
            nargs="?",
            default=None,
            type=isodate.parse_datetime,
            help="""If specified, only include data between
                    window_start_time and window_end_time.
                    Must be specified with window_end_time.
                    This option will override any default time ranges determined
                    based on potential dynamic sector times.
                            Defaults to None (include all data).""",
        )
    if arglist is None or "window_end_time" in arglist:
        sect_group.add_argument(
            "--window_end_time",
            nargs="?",
            default=None,
            type=isodate.parse_datetime,
            help="""If specified, only include data between
                    window_start_time and window_end_time.
                    Must be specified with window_start_time.
                    This option will override any default time ranges determined
                    based on potential dynamic sector times.
                            Defaults to None (include all data).""",
        )

    tc_group = parser.add_argument_group(
        title="Sector Requests: General arguments for TC sectors"
    )
    if arglist is None or "tc_spec_template" in arglist:
        tc_group.add_argument(
            "--tc_spec_template",
            nargs="?",
            default=None,
            help="""YAML plugin for creating appropriate TC sector using
                    shape/resolution from current storm location.""",
        )

    trackfile_group = parser.add_argument_group(
        title="Sector Requests: TC trackfile-based sectors"
    )
    if arglist is None or "trackfiles" in arglist:
        trackfile_group.add_argument(
            "--trackfiles",
            nargs="*",
            default=None,
            help="""Specify TC trackfiles to include in processing
                            If --trackfile_sector_list is included,
                                limit to the storms in list
                            If --trackfile_sector_list is not included,
                                process all storms""",
        )
    if arglist is None or "trackfile_parser" in arglist:
        trackfile_group.add_argument(
            "--trackfile_parser",
            nargs="?",
            default=None,
            help="""Specify TC trackfile parser to use with trackfiles, located in:
                            geoips*.plugins.modules.sector_metadata_generators .
                                myparsername.myparsername,
                            The trackfile_parser string should be the parser module
                            name (no .py)""",
        )
    if arglist is None or "trackfile_sector_list" in arglist:
        trackfile_group.add_argument(
            "--trackfile_sector_list",
            nargs="*",
            default=None,
            help="""A list of sector names found specified trackfiles to include
                    in processing. Of format: tc2020io01amphan""",
        )

    tcdb_group = parser.add_argument_group(title="Sector Requests: TC tracks database")
    if arglist is None or "tcdb_sector_list" in arglist:
        tcdb_group.add_argument(
            "--tcdb_sector_list",
            nargs="*",
            default=None,
            help="""A list of sector names found in tc database to include in
                    processing. Of format: tc2020io01amphan""",
        )
    if arglist is None or "tcdb" in arglist:
        tcdb_group.add_argument(
            "--tcdb",
            action="store_true",
            help="""Call with --tcdb to include the matching TC database sectors
                            within processing
                            If --tcdb_sector_list is also included,
                                limit the storms to those in list
                            If --tcdb_sector_list is not included,
                                process all matching storms.""",
        )

    static_group = parser.add_argument_group(
        title="Sector Requests: Static YAML sectorfiles"
    )
    if arglist is None or "sectored_read" in arglist:
        static_group.add_argument(
            "--sectored_read",
            action="store_true",
            help="""Call with --sectored_read to specify to sector the data
                            to specified area_defs during reading (ie, do not
                            read all data into memory in advance).""",
        )
    if arglist is None or "resampled_read" in arglist:
        static_group.add_argument(
            "--resampled_read",
            action="store_true",
            help="""Call with --resampled_read to specify to resample the data
                            to specified area_defs during reading (ie, do not
                            read all data into memory in advance).
                            This is required only for some geostationary readers""",
        )
    if arglist is None or "self_register_dataset" in arglist:
        static_group.add_argument(
            "--self_register_dataset",
            nargs="?",
            default=None,
            help="""Specify to register output data to the dataset specified by
                            self_register_dataset option.""",
        )
    if arglist is None or "self_register_source" in arglist:
        static_group.add_argument(
            "--self_register_source",
            nargs="?",
            default=None,
            help="""Specify to register output data to the dataset specified by
                            self_register_dataset / self_register_source options.""",
        )
    if arglist is None or "reader_defined_area_def" in arglist:
        static_group.add_argument(
            "--reader_defined_area_def",
            action="store_true",
            help="""Call with --reader_defined_area_def to specify to use only
                            area_definition defined within the reader. This option
                            supercedes all other sector-specifying options.""",
        )
    if arglist is None or "sector_list" in arglist:
        static_group.add_argument(
            "-s",
            "--sector_list",
            nargs="*",
            default=None,
            help="""A list of short sector plugin names found within YAML sectorfiles
                    over which the data file should be processed.""",
        )

    prod_group = parser.add_argument_group(title="Product specification options")
    if arglist is None or "product_name" in arglist:
        prod_group.add_argument(
            "--product_name",
            nargs="?",
            default=None,
            help="""Name of product to produce.""",
        )
    if arglist is None or "minimum_coverage" in arglist:
        prod_group.add_argument(
            "--minimum_coverage",
            nargs="?",
            default=None,
            type=float,
            help="""Minimum percent coverage required to produce product.
                            Defaults to 10.""",
        )
    if arglist is None or "product_options" in arglist:
        prod_group.add_argument(
            "--product_options",
            nargs="?",
            default=None,
            help="""Specify product specific options (these must be parsed
                            within the individual product scripts)""",
        )
    if arglist is None or "product_spec_override" in arglist:
        prod_group.add_argument(
            "--product_spec_override",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify product spec fields to override the default specifications.
                            Should be formatted as a json dictionary string""",
        )

    comp_group = parser.add_argument_group(
        title="Options for specifying output comparison"
    )
    if arglist is None or "output_file_list_fname" in arglist:
        comp_group.add_argument(
            "--output_file_list_fname",
            nargs="?",
            default=None,
            help="""Specify full path to a single file to store the complete list
                            of output files produced during the current run""",
        )

    if arglist is None or "compare_path" in arglist:
        comp_group.add_argument(
            "--compare_path",
            nargs="?",
            default=None,
            help="""Specify full path to single directory
                            (with <product> and <output> wildcards)
                            to be used for comparisons for ALL current outputs.""",
        )

    if arglist is None or "compare_paths_override" in arglist:
        comp_group.add_argument(
            "--compare_paths_override",
            nargs="?",
            default={},
            type=literal_eval,
            help="""NOT YET IMPLEMENTED Specify dictionary of full paths to directories
                            (with <product> and <output> wildcards) containing
                            output products to compare with current outputs.
                            This should be formatted as a json dictionary string, with
                            YAML output config output_types as keys, and full directory
                            comparison output path as values.  Special key "all" will
                            pertain to all output types.""",
        )

    procflow_group = parser.add_argument_group(
        title="Processing workflow specifications"
    )
    if arglist is None or "procflow" in arglist:
        if legacy:
            help_str = (
                "Specify procflow that should be followed for this file, located in "
                "geoips.plugins.modules.procflows.myprocflowname.name. The procflow "
                "string should be the procflow module file name (excluding '.py' )."
            )
        else:
            help_str = argparse.SUPPRESS
        procflow_group.add_argument(
            "--procflow",
            default=None,
            help=help_str,
        )

    if arglist is None or "filename_formatter" in arglist:
        procflow_group.add_argument(
            "--filename_formatter",
            nargs="?",
            default="geoips_fname",
            help="""Specify filename format module_name that should be used for
                            this file, where each filename_module_name is
                            'myfilemodule' where:
                                from geoips*.filenames.myfilemodule import myfilemodule
                            would be the appropriate import statement""",
        )
    if arglist is None or "filename_formatter_kwargs" in arglist:
        procflow_group.add_argument(
            "--filename_formatter_kwargs",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify filename format kwargs that should be used for
                            this filename_formatter. Should be formatted as a json
                            dictionary string""",
        )

    if arglist is None or "metadata_filename_formatter" in arglist:
        procflow_group.add_argument(
            "--metadata_filename_formatter",
            nargs="?",
            default=None,
            help="""Specify filename format module_name that should be used for
                            metadata output, where filename_module_name is
                            'myfilemodule' where:
                                geoips.filename_formatters.myfilemodule
                            would be the appropriate entry point""",
        )
    if arglist is None or "metadata_filename_formatter_kwargs" in arglist:
        procflow_group.add_argument(
            "--metadata_filename_formatter_kwargs",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify filename format kwargs that should be used for
                            this metadata_filename_formatter.
                            Should be formatted as a json dictionary string""",
        )

    if arglist is None or "output_formatter" in arglist:
        procflow_group.add_argument(
            "--output_formatter",
            nargs="?",
            default=None,
            help="""Specify output format module_name that should be used for this file,
                    each output_formatter is 'output_formatters.imagery_annotated' where
                    from geoips*.output_formatters.imagery_annotated import
                    imagery_annotated would be the appropriate import statement""",
        )
    if arglist is None or "output_formatter_kwargs" in arglist:
        procflow_group.add_argument(
            "--output_formatter_kwargs",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify output format kwargs that should be used for this
                    output_formatter. should be formatted as a json dictionary string,
                    ie: '{"title_formatter": "tc_copyright", "title_copyright": "NRL"}'
                    """,
        )

    if arglist is None or "metadata_output_formatter" in arglist:
        procflow_group.add_argument(
            "--metadata_output_formatter",
            nargs="?",
            default=None,
            help="""Specify output format module_name that should be used for
                    metadata output, each output_formatter is 'myoutputmodule' where
                        from geoips.output_formatters.myoutputmodule.myoutputmodule
                    would be the appropriate entry point""",
        )
    if arglist is None or "metadata_output_formatter_kwargs" in arglist:
        procflow_group.add_argument(
            "--metadata_output_formatter_kwargs",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify output format kwargs that should be used for this metadata.
                    Should be formatted as a json dictionary string.""",
        )

    if arglist is None or "output_config" in arglist:
        procflow_group.add_argument(
            "--output_config",
            nargs="?",
            default=None,
            help="""Specify YAML config file holding output modile names and
                                          their respective filename modules""",
        )

    if arglist is None or "no_presectoring" in arglist:
        procflow_group.add_argument(
            "--no_presectoring",
            action="store_true",
            help="""If true, do not pre-sector data prior to running the algorithm.
                    This is less efficient, but allows the original dataset to
                    be passed to the algorithm in full.""",
        )

    if arglist is None or "output_checker_name" in arglist:
        procflow_group.add_argument(
            "--output_checker_name",
            default=None,
            help="""Output Checker Name Override.
                    - By default, GeoIPS determines the appropriate
                      output_checker plugin to use for comparisons based on
                      the file extension of the output.
                    - If a particular file extension is not explicitly
                      supported, but is expected to be able to utilize one of
                      the existing output checkers (e.g. using the "text"
                      output checker with a CSV file), this argument allows the
                      name of the checker to be passed in to override the default.
                    - I.e., to force the use of the "text" ouput checker with a
                      product that produces a CSV output output_checker plugin,
                      you would pass:
                        --output_checker_name text
                    """,
        )

    if arglist is None or "output_checker_kwargs" in arglist:
        procflow_group.add_argument(
            "--output_checker_kwargs",
            default={},
            type=literal_eval,
            help="""Output Checker Keyword Arguments.
                    - These keyword arguments get passed through directly to the
                      outputs_match method on the output_checker plugin.
                    - This should be formatted as a json dictionary string,
                      with the first level being the plugin name that the
                      keyword arguments apply to, and the second level being
                      a dictionary of keyword argument name/value pairs.
                    - Ie, for the "threshold" keyword argument in the "image"
                      output_checker plugin, you would pass:
                        --output_checker_kwargs '{"image": {"threshold": "0.05"}}'
                    """,
        )

    rdr_group = parser.add_argument_group(title="Data reader specifications")

    if arglist is None or "reader_name" in arglist:
        rdr_group.add_argument(
            "--reader_name",
            default=None,
            help="""If --reader_name is passed, the specific reader will be located in
                    geoips*.readers.myreader_name.myreader_name,
                    The reader_name string should be the reader module name (no .py)""",
        )
    if arglist is None or "reader_kwargs" in arglist:
        sect_group.add_argument(
            "--reader_kwargs",
            nargs="?",
            default=None,
            type=literal_eval,
            help="""Specify reader kwargs that should be used for
                            this reader. Should be formatted as a json
                            dictionary string""",
        )

    if arglist is None or "bg_product_name" in arglist:
        rdr_group.add_argument(
            "--bg_product_name",
            default=None,
            help="""Product to use for background imagery""",
        )
    if arglist is None or "bg_reader_name" in arglist:
        rdr_group.add_argument(
            "--bg_reader_name",
            default=None,
            help="""If --bg_reader_name is passed, the specific reader will be located
                    in geoips*.readers.myreader_name.myreader_name, The bg_reader_name
                    string should be the reader module name (no .py)""",
        )
    if arglist is None or "bg_fnames" in arglist:
        rdr_group.add_argument(
            "--bg_fnames",
            nargs="*",
            default=None,
            help="""Specify filenames to use for background imagery.
                    If --bg_reader_name included, use specific reader for
                    reading background datafiles.""",
        )

    plt_group = parser.add_argument_group(title="Plotting parameter specifications")
    if arglist is None or "gridline_annotator" in arglist:
        plt_group.add_argument(
            "--gridline_annotator",
            default=None,
            help="""If --gridline_annotator is passed, the specific gridline
                    params will be located in
                    geoips*.image_utils.plotting_params.gridlines.gridline_annotator,
                    The gridline_annotator string should be the base gridline name
                    (no .yaml)""",
        )
    if arglist is None or "feature_annotator" in arglist:
        plt_group.add_argument(
            "--feature_annotator",
            default=None,
            help="""If --feature_annotator is passed, the specific feature
                    annotations will be located in
                    geoips*.plugins.yaml.feature_annotators.<feature_annotator>,
                    The feature_annotator string should be the base feature annotator
                    name (no .yaml)""",
        )

    if arglist is None or "model_reader_name" in arglist:
        rdr_group.add_argument(
            "--model_reader_name",
            default=None,
            help="""If --model_reader_name is passed, the specific reader
                    will be located in
                    geoips*.readers.my_reader_name.my_reader_name,
                    The model_reader_name string should be the reader module name
                    (no .py)""",
        )
    if arglist is None or "model_fnames" in arglist:
        rdr_group.add_argument(
            "--model_fnames",
            nargs="*",
            default=None,
            help="""Specify filenames to use for NWP model data.
                    If --model_reader_name included, use specific reader for
                    reading model datafiles.""",
        )
    if arglist is None or "buoy_reader_name" in arglist:
        rdr_group.add_argument(
            "--buoy_reader_name",
            default=None,
            help="""If --buoy_reader_name is passed, the specific reader
                    will be located in
                    geoips*.readers.my_reader_name.my_reader_name,
                    The buoyreadername string should be the reader module name
                    (no .py)""",
        )
    if arglist is None or "buoy_fnames" in arglist:
        rdr_group.add_argument(
            "--buoy_fnames",
            nargs="*",
            default=None,
            help="""Specify filenames to use for buoy data.
                    If --buoy_reader_name included, use specific reader for
                    reading buoy datafiles.""",
        )
    if arglist is None or "aeorsol_reader_name" in arglist:
        rdr_group.add_argument(
            "--aerosol_reader_name",
            default=None,
            help="""If --model_reader_name is passed, the specific reader
                    will be located in
                    geoips*.readers.my_reader_name.my_reader_name,
                    The model_reader_name string should be the reader module name
                    (no .py)""",
        )
    if arglist is None or "aerosol_fnames" in arglist:
        rdr_group.add_argument(
            "--aerosol_fnames",
            nargs="*",
            default=None,
            help="""If --aerosol_reader_name included, use specific reader for
                    reading aerosol model datafiles.""",
        )

    fusion_group = parser.add_argument_group(
        title="Options for specifying fusion products"
    )
    if arglist is None or "fuse_files" in arglist:
        fusion_group.add_argument(
            "--fuse_files",
            action="append",
            nargs="+",
            default=None,
            help="""Provide additional files required for fusion product.
                    Files passed under this flag MUST be from the same source.
                    fuse_files may be passed multiple times.  Reader name for
                    these files is specified with the fuse_reader flag.""",
        )
        fusion_group.add_argument(
            "--fuse_reader",
            action="append",
            default=None,
            help="""Provide the reader name for files passed under the
                    fuse_files flag. Only provide one reader to this flag.
                    If multiple fuse_files flags are passed, the same number of
                    fuse_readers must be passed in the same order.""",
        )
        fusion_group.add_argument(
            "--fuse_reader_kwargs",
            action="append",
            default=None,
            type=literal_eval,
            help="""Provide the reader kwargs for files passed under the
                    fuse_files flag. Should be formatted as a json dictionary string.
                    Only provide one json dict str to this flag.
                    If multiple fuse_files flags are passed, the same number of
                    fuse_reader_kwargs must be passed in the same order.""",
        )
        fusion_group.add_argument(
            "--fuse_product",
            action="append",
            default=None,
            help="""Provide the product name for files passed under the
                    fuse_files flag. Only provide one product to this flag.
                    If multiple fuse_files flags are passed, the same number of
                    fuse_products must be passed in the same order.""",
        )
        fusion_group.add_argument(
            "--fuse_resampled_read",
            action="append",
            default=None,
            help="""Identify whether the reader specified for
                    --fuse_files / --fuse_reader perform a resampled_read.
                    If not specified, a resampled read will NOT be performed.
                    If multiple fuse_files flags are passed, either the same
                    number of fuse_resampled_read flags must be passed in the
                    same order, or no fuse_resampled_read flags can be passed.""",
        )
        fusion_group.add_argument(
            "--fuse_sectored_read",
            action="append",
            default=None,
            help="""Identify whether the reader specified for --fuse_files/--fuse_reader
                    perform a sectored_read.  If not specified, a sectored_read will NOT
                    be performed.  If multiple fuse_files flags are passed, either
                    the same number of fuse_sectored_read flags must be passed
                    in the same order, or no fuse_sectored_read flags can be passed.""",
        )
        fusion_group.add_argument(
            "--fuse_self_register_dataset",
            action="append",
            default=None,
            help="""Identify the DATASET of the data to which the associated
                    fuse_files should be registerd. If not specified, data will
                    not be registered to a dataset, but the requested area_def.
                    If multiple fuse_files flags are passed, either the same
                    number of fuse_self_register_dataset flags must be passed in
                    the same order, or no fuse_self_register_dataset flags can
                    be passed.""",
        )
        fusion_group.add_argument(
            "--fuse_self_register_source",
            action="append",
            default=None,
            help="""Identify the SOURCE of the data to which the associated
                    fuse_files should be registerd If not specified, data will
                    not be registered to a dataset, but the requested. area_def.
                    If multiple fuse_files flags are passed, either the same
                    number of fuse_self_register_source flags must be passed in
                    the same order, or no fuse_self_register_source flags can be
                    passed.""",
        )
        fusion_group.add_argument(
            "--fuse_self_register_platform",
            action="append",
            default=None,
            help="""Identify the SOURCE of the data to which the associated
                    fuse_files should be registerd. If not specified, data will
                    not be registered to a dataset, but the requested area_def.
                    If multiple fuse_files flags are passed, either the same
                    number of fuse_self_register_source flags must be passed in
                    the same order, or no fuse_self_register_source flags can be
                    passed.""",
        )

    prod_db_group = parser.add_argument_group(title="Product database specifications")
    if arglist is None or "product_db" in arglist:
        prod_db_group.add_argument(
            "--product_db",
            action="store_true",
            help="Use product database to store product paths created by the procflow",
        )
        prod_db_group.add_argument(
            "--product_db_writer",
            default=None,
            help="""If --product_db_writer is passed, the specific product
                    database writer will be located in
                    geoips*.plugins.modules.postgres_database.
                        mywriter_name.mywriter_name,
                    The writer_name string should be the reader module name
                    (no .py)""",
        )
        prod_db_group.add_argument(
            "--product_db_writer_kwargs",
            default=None,
            type=literal_eval,
            help="""Provide the product db writer kwargs for the plugin passed under the
                    product_db_writer flag. Should be formatted as a json dictionary
                    string. Only provide one json dict str to this flag.""",
        )
        prod_db_group.add_argument(
            "--product_db_writer_override",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify product database writer that should be used for each
                    available sector should be formatted as a json dictionary
                    string.""",
        )
        prod_db_group.add_argument(
            "--store_checkpoint_statistics",
            action="store_true",
            help="""Store the tracked resource usage statistics for each checkpoint to
                    the backend database.""",
        )

    composite_group = parser.add_argument_group(title="Image composite kwargs")
    if arglist is None or "composite_output_kwargs_override" in arglist:
        composite_group.add_argument(
            "--composite_output_kwargs_override",
            nargs="?",
            default={},
            type=literal_eval,
            help="""Specify product composite kwargs that should be used for each
                    available sector output. Should be formatted as a json dictionary
                    string.""",
        )
