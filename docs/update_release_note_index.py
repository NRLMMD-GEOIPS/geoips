#!/bin/env python
from sys import argv, exit

index_filename = argv[1]
add_version = argv[2]

# Eventually we will likely support actual versions or latest.  For now only
# support "latest".
# This may end up being just auto-generating the ENTIRE index.rst, which will
# remove the need for specifying a version at all.  For now we are only adding
# the "latest" section to index.rst so the doc build doesn't fail from a non-existent
# reference.  In order to auto-generate the entire index.rst, we would have to
# include the high level minor release version summaries somewhere outside index.rst
# (right now the only specification of the high level summaries is in index.rst,
# so we can't entirely auto-generate it).
# This will be revisited after the 2024 workshop.  For now this will work.
if add_version != "latest":
    print("Actual versions not yet supported - only latest")
    exit(1)
    # Something like this for adding actual version to index.rst
    # Or we may just auto-generate the entire index.rst
    # major, minor, bug_fix = add_version.split(".")
    # minor_version = f"{major}.{minor}"
    # release_note_version = f"v{add_version.replace(".", "_")}"
with open(index_filename, "r") as fobj:
    first = True
    new_lines = []
    last_line = None
    for line in fobj.readlines():
        # Make sure we write all the lines back out
        if "----" not in line or not first:
            if last_line:
                new_lines += [last_line]
        # When we get to the first header ----- line, that means we need to
        # add the new "minor release" section (at the top).
        # If we end up auto-generating the entire index.rst, this will change
        # (since we'll just loop through all the release notes, and write out
        # the sections one by one.  We wouldn't have to keep track of where we
        # were at all).
        if "----" in line and first:
            if add_version == "latest":
                first = False
                new_lines += ["Latest (version on cutting edge of git)\n"]
                new_lines += ["---------------------------------------\n"]
                new_lines += ["\n"]
                new_lines += [".. toctree::\n"]
                new_lines += ["   :maxdepth: 1\n"]
                new_lines += ["\n"]
                new_lines += ["   latest\n"]
                new_lines += ["\n"]
                new_lines += [last_line]
            # Something like this to add actual version to index.rst
            # elif last_line != f"Version {minor_version}":
            #     new_lines += ["Version {minor_version}"]
            #     new_lines += ["-----------------------"]
            #     new_linst += [""]
        last_line = line

    new_lines += [last_line]
# Now write all the lines back out, with the new "latest" section inserted.
with open(index_filename, "w") as fobj:
    fobj.writelines(new_lines)
