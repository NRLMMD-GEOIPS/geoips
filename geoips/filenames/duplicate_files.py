# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module to handle removing duplicate files, based on filename formats.

If an individual filename format has a method named
``"<filename_formatter>_remove_duplicates"``
defined, use that method to remove duplicates for the given current filename.
"""

import logging

LOG = logging.getLogger(__name__)


def remove_duplicates(fnames, remove_files=False):
    """Remove duplicate files from all filenames included in dict fnames.

    Parameters
    ----------
    fnames : dict
        Dictionary with individual filenames as keys, and a field named
        "filename_formatter" which indicates the filename format used to
        generate the given filename.
    remove_files : bool, optional
        Specify whether to remove files (True), or just list what would have
        been removed, default to False

    Returns
    -------
    removed_files : list
        List of files that were removed.
    saved_files : list
        List of files that were not removed.
    """
    removed_files = []
    saved_files = []
    from geoips.interfaces import filename_formatters
    from importlib import import_module

    for fname in fnames:
        if "filename_formatter" not in fnames[fname]:
            LOG.info("SKIPPING %s, no filename_formatter defined", fname)
            saved_files += [fname]
            continue
        filename_formatter = fnames[fname]["filename_formatter"]
        fname_fmt_plugin = filename_formatters.get_plugin(
            fnames[fname]["filename_formatter"]
        )
        if hasattr(
            import_module(fname_fmt_plugin.__module__),
            f"{filename_formatter}_remove_duplicates",
        ):
            fnamer_remove_dups = getattr(
                import_module(fname_fmt_plugin.__module__),
                f"{filename_formatter}_remove_duplicates",
            )
            curr_removed_files, curr_saved_files = fnamer_remove_dups(
                fname, remove_files=remove_files
            )
            removed_files += curr_removed_files
            saved_files += curr_saved_files
        else:
            LOG.warning(
                "SKIPPING DUPLICATE REMOVAL no "
                f"{filename_formatter}_remove_duplicates defined"
            )

    return removed_files, saved_files
