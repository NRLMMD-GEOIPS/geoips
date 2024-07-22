#!/bin/env python
import os
from glob import glob
from sys import argv, exit

index_filename=argv[1]
add_version = argv[2]
if add_version != "latest":
    print("Actual versions not yet supported - only latest")
    exit(1) 
    # Something like this for adding actual version to index.rst
    # major, minor, bug_fix = add_version.split(".")
    # minor_version = f"{major}.{minor}"
    # release_note_version = f"v{add_version.replace(".", "_")}"
with open(index_filename, "r") as fobj:
    first = True
    new_lines = []
    last_line = None
    for line in fobj.readlines():
        if "----" not in line or not first:
            if last_line:
                new_lines += [last_line]
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
with open(index_filename, "w") as fobj:
    fobj.writelines(new_lines)
