#!/bin/env python

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Update release note index with latest version release reference."""
from sys import argv
from glob import glob
from pathlib import Path
from os.path import basename, exists


def main(index_filename, release_note_path):
    """Generate an index.rst file for release notes.

    This function scans the specified directory for release note files, sorts them based
    on version numbers (and alpha releases), and generates an
    ``index.rst`` file that includes a table of contents.

    Parameters
    ----------
    index_filename : str or Path
        The path to the output ``index.rst`` file to be generated.
    release_note_path : str or Path
        The directory containing release note ``.rst`` files.

    Notes
    -----
    The function processes release note files that match the following naming patterns:

    - ``vX_Y_Z.rst``
    - ``vX_Y_ZaN.rst``
    - ``X.Y.Z.rst``
    - ``X.Y.ZaN.rst``

    where ``X``, ``Y``, ``Z``, and ``N`` are integers representing the major, minor,
    bugfix, and alpha version numbers, respectively.

    Release notes not matching these patterns are ignored.

    If a file named ``latest.rst`` exists in the ``release_note_path``, it is included
    at the top of the generated index under the heading "Latest (version on cutting edge
    of git)".

    It excludes ``index.rst`` and ``latest.rst`` from the list of release notes
    to be processed (except for including ``latest.rst`` at the top if it exists).

    The release notes are sorted in reverse chronological order (newest first) based on
    their version numbers.

    The function does not include high-level version summaries from
    ``version_summaries.yaml``; these are not currently populated in ``index.rst``.
    These will be included when brassy takes over this functionality.

    Examples
    --------
    Generate an ``index.rst`` file from release notes in ``docs/releases``:

    >>> from pathlib import Path
    >>> index_file = 'docs/releases/index.rst'
    >>> release_notes_dir = 'docs/releases'
    >>> main(index_file, release_notes_dir)
    """
    index_filename = Path(index_filename)
    release_note_path = Path(release_note_path)
    # Note this does NOT include the high level version summaries - those live
    # in docs/source/releases/version_summaries.yaml, but are not currently being
    # populated in index.rst.  When this release note index creation is moved to
    # brassy, the version summaries will be pulled from version_summaries.yaml
    # to include in the index.rst.

    # Note this will sort release notes properly named as:
    # * vX_Y_Z.rst
    # * vX_Y_ZaN.rst
    # * X.Y.Z.rst
    # * X.Y.ZaN.rst

    # Includes "latest" at the top if it exists.

    # No other release note name formatting supported.

    # Include standard top level headers
    lines = [".. dropdown:: Distribution Statement\n"]
    lines += ["\n"]
    lines += [" | This is an auto-generated file.\n"]
    lines += [" | Please abide by license packaged with this software.\n"]
    lines += ["\n"]
    lines += [".. _release_notes:\n"]
    lines += ["\n"]
    lines += ["Release Notes\n"]
    lines += ["*************\n"]
    lines += ["\n"]

    # If latest.rst exists, include it in the index.rst
    if exists(str(release_note_path / "latest.rst")):
        lines += ["Latest (version on cutting edge of git)\n"]
        lines += ["---------------------------------------\n"]
        lines += ["\n"]
        lines += [".. toctree::\n"]
        lines += ["   :maxdepth: 1\n"]
        lines += ["\n"]
        lines += ["   latest\n"]
        lines += ["\n"]

    # If upcoming.rst exists, include it in the index.rst
    if exists(str(release_note_path / "upcoming.rst")):
        lines += ["Upcoming (version AHEAD OF the cutting edge of git)\n"]
        lines += ["---------------------------------------------------\n"]
        lines += ["\n"]
        lines += [".. toctree::\n"]
        lines += ["   :maxdepth: 1\n"]
        lines += ["\n"]
        lines += ["   upcoming\n"]
        lines += ["\n"]

    # Collect all the major, minor, bugfix, alpha version numbers, in a sortable
    # manner
    versions = {}
    # List all the release notes of format v*.rst - ie, don't include index.rst
    # or latest.rst, but DO include X_Y_ZaN.rst (alpha releases)
    for rst_file in glob(str(release_note_path / "*.rst")):
        if basename(rst_file) in ["latest.rst", "index.rst", "upcoming.rst"]:
            continue
        # print(f"Adding {rst_file}")
        # Just leave X.Y.ZaN or X.Y.Z, as appropriate
        # This will work with vX_Y_Z.rst, vX_Y_ZaN.rst, X.Y.Z.rst, or X.Y.ZaN.rst
        version_num = (
            basename(rst_file).replace("v", "").replace(".rst", "").replace("_", ".")
        )
        # print(f"verson {version_num}")
        # Default alpha to None and mmb (major/minor/bugfix) to version_num -
        # alpha not defined for full releases.
        alpha = None
        mmb_version_num = version_num
        # If there is an "a" in version_num, ie X_Y_ZaN, ensure we capture the
        # appropriate alpha version, and remove the aN from the mmb_version_num
        if "a" in version_num:
            mmb_version_num, alpha = version_num.split("a")
        # Now split for major/minor/bugfix from the X_Y_Z version
        major, minor, bugfix = mmb_version_num.split(".")
        # Zero pad these for sorting
        major = f"{int(major):03}"
        minor = f"{int(minor):03}"
        bugfix = f"{int(bugfix):03}"

        # Only include alpha if it is defined.
        if alpha is not None:
            alpha = f"{int(alpha):03}"
        # Store these in dictionaries so we can loop through in order
        if major not in versions:
            versions[major] = {}
        if minor not in versions[major]:
            versions[major][minor] = {}
        if bugfix not in versions[major][minor]:
            versions[major][minor][bugfix] = []
        # If alphas are defined, store them in a list at the lowest level.
        if alpha is not None:
            versions[major][minor][bugfix] += [alpha]

    # Now loop through major, minor, bugfix, and alpha, appending sections
    # in order as appropriate.
    for major in sorted(versions, reverse=True):
        for minor in sorted(versions[major], reverse=True):
            print(f"Adding {int(major)}.{int(minor)}")
            version_header = f"Version {int(major)}.{int(minor)}"
            version_underline = "-" * (len(version_header))
            lines += [f"{version_header}\n"]
            lines += [f"{version_underline}\n"]
            lines += ["\n"]
            lines += [".. toctree::\n"]
            lines += ["   :maxdepth: 1\n"]
            lines += ["\n"]
            for bugfix in sorted(versions[major][minor], reverse=True):
                curr_mmb = f"v{int(major)}_{int(minor)}_{int(bugfix)}"
                curr_mmb_period = f"{int(major)}.{int(minor)}.{int(bugfix)}"
                # Only add major/minor/bugfix version if it exists - could be
                # an alpha release with NO MMB release.
                if exists(str(release_note_path / f"{curr_mmb}.rst")):
                    lines += [f"   {curr_mmb}\n"]
                elif exists(str(release_note_path / f"{curr_mmb_period}.rst")):
                    lines += [f"   {curr_mmb_period}\n"]
                for alpha in sorted(versions[major][minor][bugfix], reverse=True):
                    if exists(str(release_note_path / f"{curr_mmb}a{int(alpha)}.rst")):
                        lines += [f"   {curr_mmb}a{int(alpha)}\n"]
                    elif exists(
                        str(release_note_path / f"{curr_mmb_period}a{int(alpha)}.rst")
                    ):
                        lines += [f"   {curr_mmb_period}a{int(alpha)}\n"]
            lines += ["\n"]
    # Now write all the lines we've collected out to index.rst
    with open(index_filename, "w") as fobj:
        print(f"Writing {index_filename}")
        fobj.writelines(lines)


if __name__ == "__main__":
    main(argv[1], argv[2])
