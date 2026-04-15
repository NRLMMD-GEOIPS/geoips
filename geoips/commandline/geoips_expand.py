# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "expand" command.

Single 'geoips expand <workflow_name>' command which will fully expand a workflow in the
case it has embedded workflows or products included in its steps.
"""

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
import yaml

from geoips.commandline.geoips_command import GeoipsExecutableCommand
from geoips.interfaces import workflows


class GeoipsExpand(GeoipsExecutableCommand):
    """Tree Command Class for displaying GeoIPS CLI commands in a tree-like fashion.

    Can be configured to print in a colored fashion, up to a maximum depth, and whether
    or not we want the full command string or just the command name at it's depth.

    Where depth denotes the level of the command you'd like to display.
    I.e. <0> geoips <1> list <2> scripts
    """

    name = "expand"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the tree-subparser for the Tree Command."""
        self.parser.add_argument(
            "workflow_name",
            type=str,
            help="Name of the workflow plugin to expand.",
        )
        self.parser.add_argument(
            "--color",
            default=False,
            action="store_true",
            help="Whether or not we want to highlight the output of this command.",
        )

    def __call__(self, args):
        """Run the `geoips tree <opt_args>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        print()
        workflow_name = args.workflow_name
        workflow = workflows.get_plugin(workflow_name, _expand=True)

        formatted_wf = yaml.dump(
            workflow, indent=2, default_flow_style=False, sort_keys=False
        )

        if args.color:
            lexer = get_lexer_by_name("yaml")
            highlighted = highlight(formatted_wf, lexer, TerminalFormatter())
            print(highlighted)
        else:
            print(formatted_wf)
