"""Unit test asserting functionality for exposing plugin-package commands."""

from importlib.resources import files
import logging
import pytest
import toml

from geoips.errors import PackageNotFoundError
from geoips.geoips_utils import (
    expose_geoips_commands,
    _get_pyproj_scripts,
    get_entry_point_group,
)

LOG = logging.getLogger(__name__)

plugin_packages = [
    str(ep.value) for ep in get_entry_point_group("geoips.plugin_packages")
]


def generate_id(pkg_name):
    """Generate a test ID for the provided plugin package."""
    return f"expose {pkg_name}"


@pytest.mark.parametrize(
    "pkg_name", plugin_packages + ["non_existent_pkg"], ids=generate_id
)
def test_expose_pkg_cmds(pkg_name, caplog):
    """Assert various calls to 'expose_geoips_commands' work as expected.

    Parameters
    ----------
    pkg_name: str
        - The name of the plugin package whose command's that will be exposed
    caplog: pytest caplog fixture
        - Pytest fixture which captures the log from the corresponding calls
    """
    # 35 is the level of LOG.interactive, which we use in expose_geoips_commands
    caplog.set_level(35)
    if pkg_name in ["geoips", "data_fusion"]:
        # Both of these packages have commands. geoips is implemented via poetry, and
        # data_fusion is implemented via setuptools. Either way, this should work
        # without an error being raised
        expose_geoips_commands(pkg_name, LOG)
        assert f"Available {pkg_name.title()} Commands" in caplog.text
        with open(files(pkg_name) / "../pyproject.toml", "r") as toml_file:
            pyproj = toml.load(toml_file)
            scripts = _get_pyproj_scripts(pyproj)
        for name, cmd in scripts.items():
            # Replace calls are needed as we need to filter out the table chars
            # if the table was split due to terminal size
            assert name in caplog.text.replace("\n", "").replace(" ", "").replace(
                "-",
                "",
            ).replace("│", "")
            assert cmd in caplog.text.replace("\n", "").replace(" ", "").replace(
                "-",
                "",
            ).replace("│", "")

    elif pkg_name in plugin_packages:
        # None of these packaes have commands
        expose_geoips_commands(pkg_name, LOG)
        assert f"No '{pkg_name.title()}' Commands were found." in caplog.text

    else:
        # Calling this with a non-existent package should raise PackageNotFoundError
        with pytest.raises(PackageNotFoundError):
            expose_geoips_commands(pkg_name, LOG)
    caplog.clear()
