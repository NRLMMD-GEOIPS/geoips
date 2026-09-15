# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Create the support files for versioned docs.

This includes:
- the `versions.json` file which drives the `pydata-sphinx-theme`'s version switcher
- the symlink `stable` to the latest minor release family
- a root-level `index.html` that redirects to `/stable`
- a root-level `404.html` that redirects URLs without a version string to the matching
  path on `stable`
"""

import argparse
import json
from pathlib import Path
import re
from typing import List, Dict, Union
import warnings

from packaging import Version


# Presume open source geoips github pages link as default
DEFAULT_BASE_URL = "https://nrlmmd-geoips.github.io/geoips/"
# Consider directories starting with a v then a digit as a docs version directory
VERSION_PATTERN = re.compile("^v[0-9]")
# Static HTML for the two redirect files (with the latter modeled after GitHub Pages'
# default)
HTML_INDEX_REDIRECT = """<html>
    <head><meta http-equiv="Refresh" content="0;url=stable/"></head>
    <body><p>Redirecting to stable...</p></body>
</html>"""
HTML_404_REDIRECT = """<html>
<head>
    <title>404 · Page Not Found · GitHub Pages</title>
    <style>
        body {
            background-color: #f1f1f1;
            margin: 0;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        }
        .container {
            margin: 50px auto 40px auto;
            width: 600px;
            text-align: center;
        }
        a {
            color: #4183c4;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        h1 {
            width: 800px;
            position:relative;
            left: -100px;
            letter-spacing: -1px;
            line-height: 60px;
            font-size: 60px;
            font-weight: 100;
            margin: 0px 0 50px 0;
            text-shadow: 0 1px 0 #fff;
        }
        p {
            color: rgba(0, 0, 0, 0.5);
            margin: 20px 0;
            line-height: 1.6;
        }
        #suggestions {
            margin-top: 35px;
            color: #ccc;
        }
        #suggestions a {
            color: #666666;
            font-weight: 200;
            font-size: 14px;
            margin: 0 10px;
        }
    </style>
    <script>
        (() => {
        var parts = location.pathname.replace(/^\/+|\/+$/g, "").split("/");
        var [packageName, firstPathPart, ...otherParts] = parts;
        var isVersioned = /^(stable|dev|v\d+\.\d+)$/.test(firstPathPart || "");

        if (packageName && firstPathPart && !isVersioned) {
            tailingPathname = [firstPathPart, ...otherParts].join("/") + location.hash;
            location.replace(`/${packageName}/stable/${tailingPathname}`);
        }
        })();
    </script>
</head>
<body><div class="container">
    <h1>404</h1>
    <p><strong>Page not found</strong></p>
    <p>The requested documentation page cannot be found.</p>
    <div id="suggestions">
        <a href="https://github.com/NRLMMD-GEOIPS/geoips/">GeoIPS on GitHub</a>
    </div>
</div></body>
</html>"""


def scan_for_directories(scan_path: Path) -> List[str]:
    """Locate all first-level subdirectories matching the pattern for a docs version.

    Parameters
    ----------
    scan_path : Path
        The parent directory to scan for version subdirectories.

    Returns
    -------
    list
        List of strings with the subdirectory names matching the version pattern.
    """
    all_subdirs = [
        str(p.relative_to(scan_path)) for p in scan_path.iterdir() if p.is_dir()
    ]
    return [p for p in all_subdirs if VERSION_PATTERN.search(p)]


def create_version_config(
    versions: List[str], base_url: str
) -> List[Dict[str, Union[str, bool]]]:
    """Generate the sphinx theme version switcher's configuration for JSON output.

    Parameters
    ----------
    versions : list
        List of strings of version directories (i.e., "vX.Y" format) to include in the
        version switcher dropdown configuration file.
    base_url : str
        URL string to prepend to all subdirectory paths (should typically be of the
        format "https://{{ORG_NAME}}.github.io/{{REPO_NAME}}/").

    Returns
    -------
    list
        List of dictionaries containing the configuration options for the version
        switcher.

    Notes
    -----
    More information about the configuration format can be found at `the PyData Theme's
    docs <https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/version-dropdown.html#add-a-json-file-to-define-your-switcher-s-versions>`.
    """
    # Initial config, always include stable and dev
    config = [
        {
            "version": "stable",
            "url": f"{base_url}stable/",
            "is_latest": True
        },
        {
            "version": "dev",
            "url": f"{base_url}dev/"
        },
    ]
    # Now, add the directories, sorted by version
    for version_dir in sorted(versions, lambda v: Version(v[1:])):
        config.append({
            "name": version_dir,
            "version": version_dir[1:],
            "url": f"{base_url}{version_dir}/"
        })
    return config


def write_versions_json(config: List[Dict[str, Union[str, bool]]], output_path: Path):
    """Write a version switcher configuration to a versions.json file.

    Parameters
    ----------
    config : list
        List of dictionaries containing sphinx theme version switcher details.
    output_path : Path
        Path to which to write the versions.json file.
    """
    with (output_path / "versions.json").open("w") as f:
        json.dump(config, f)


def write_html_redirect(output_path: Path, which="index"):
    """Write an html file for redirecting either root or missing URLs to stable.

    Parameters
    ----------
    output_path : Path
        ...
    which : {'index', '404'}
        Whether to create the index or 404 file.
    """
    if which == "index":
        html = HTML_INDEX_REDIRECT
        fname = "index.html"
    elif which == "404":
        html = HTML_404_REDIRECT
        fname = "404.html"
    else:
        raise ValueError("Unsupported redirect option given to `which` argument.")
    with (output_path / fname).open("w") as f:
        f.write(html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create support files for versioned docs"
    )

    parser.add_argument(
        "-S",
        "--scan-dir",
        type=Path,
        help=(
            "Path containing version directories to parse (required for "
            "--create-version-file or --create-stable-symlink)"
        ),
        default=argparse.SUPPRESS
    )
    parser.add_argument(
        "-O",
        "--output-dir",
        type=Path,
        help="Output Path",
        required=True
    )
    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL to which GitHub Pages for this package deploys to",
        default=DEFAULT_BASE_URL
    )
    parser.add_argument(
        "--create-version-file",
        action="store_true",
        help="Create versions.json file in output dir"
    )
    parser.add_argument(
        "--create-stable-symlink",
        action="store_true",
        help="Create symlink `stable` to latest (non-dev) directory"
    )
    parser.add_argument(
        "--create-index-redirect",
        action="store_true",
        help="Create an index.html containing a meta-redirect to `stable`"
    )
    parser.add_argument(
        "--create-404-redirect",
        action="store_true",
        help=(
            "Create a 404.html containing JS redirect of non-versioned paths to the "
            "equivalent on `stable`"
        )
    )

    args = parser.parse_args()

    # Validate inputs
    if (
        (args.create_version_file or args.create_stable_symlink)
        and not hasattr(args, "scan_dir")
    ):
        raise ValueError((
            "Version file and/or stable symlink cannot be created without an input "
            "--scan-dir"
        ))
    if not args.base_url.endswith("/"):
        raise ValueError("--base-url must have a trailing slash to be valid")

    version_dirs = (
        scan_for_directories(args.scan_dir) if hasattr(args, "scan_dir") else None
    )

    if args.create_version_file:
        if not len(version_dirs):
            warnings.warn((
                "No version directories found, writing dev-only config. Ensure you "
                "specified the correct directory..."
            ))
            config = {"version": "dev", "url": f"{args.base_url}dev/"}
        else:
            config = create_version_config(version_dirs, args.base_url)
        write_versions_json(config, args.output_dir)
        print((
            f"{len(config)} version dropdown options now included in "
            f"{args.output_dir}/versions.json"
        ))

    if args.create_stable_symlink:
        try:
            latest = sorted(version_dirs, lambda v: Version(v[1:]))[-1]
        except IndexError:
            raise ValueError((
                "Specified --scan-dir contains no valid version directories, and so "
                "cannot symlink the most recent"
            ))
        (args.output_dir / "stable").symlink_to(
            args.output_dir / latest, target_is_directory=True
        )
        print(f"Symlinked {latest} as stable")

    if args.create_index_redirect:
        write_html_redirect(args.output_dir, which="index")
        print("index.html created")

    if args.create_404_redirect:
        write_html_redirect(args.output_dir, which="404")
        print("404.html created")
