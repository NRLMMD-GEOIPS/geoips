# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test asserting functionality for exposing plugin-package commands."""

from importlib import metadata
import logging
import pytest

from geoips.errors import PluginPackageNotFoundError
from geoips.geoips_utils import expose_geoips_commands

LOG = logging.getLogger(__name__)

plugin_packages = [
    str(ep.value) for ep in metadata.entry_points(group="geoips.plugin_packages")
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
    eps = list(
        filter(
            lambda ep: pkg_name in ep.value,
            metadata.entry_points().select(group="console_scripts"),
        )
    )
    if len(eps):
        # Both of these packages have commands. geoips is implemented via poetry, and
        # data_fusion is implemented via setuptools. Either way, this should work
        # without an error being raised
        expose_geoips_commands(pkg_name, LOG)
        assert f"Available {pkg_name.title()} Commands" in caplog.text
        # Replace calls are needed as we need to filter out the table chars
        # if the table was split due to terminal size
        replaced = str(
            caplog.text.replace("\n", "")
            .replace(" ", "")
            .replace(
                "-",
                "",
            )
            .replace("│", "")
        )
        for ep in eps:
            assert ep.name in replaced  # name of the command
            assert ep.value in replaced  # path to the command
    elif pkg_name in plugin_packages:
        # None of these packaes have commands
        expose_geoips_commands(pkg_name, LOG)
        assert f"No '{pkg_name.title()}' Commands were found." in caplog.text
    else:
        # Calling this with a non-existent package should raise PackageNotFoundError
        with pytest.raises(PluginPackageNotFoundError):
            expose_geoips_commands(pkg_name, LOG)
    caplog.clear()
