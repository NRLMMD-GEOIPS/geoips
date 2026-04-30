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
    """Expand command class for fully dumping a workflow plugin to the terminal.

    This should be used to confirm the order of steps applied in a workflow plugin.
    Since embedded workflows and products can be included in workflow plugins, it's not
    always easy to see the order of operations that will be applied from a top-level
    workflow plugin. This is an easy way to mitigate that.
    """

    name = "expand"
    command_classes = []

    def add_arguments(self):
        """Add arguments to the expand-subparser for the Expand Command."""
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
        """Run the `geoips expand <workflow-name>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        print()
        workflow_name = args.workflow_name
        workflow = workflows.get_plugin(workflow_name, _expand=True)

        formatted_wf = yaml.dump(
            dict(workflow), indent=2, default_flow_style=False, sort_keys=False
        )

        if args.color:
            lexer = get_lexer_by_name("yaml")
            highlighted = highlight(formatted_wf, lexer, TerminalFormatter())
            print(highlighted)
        else:
            print(formatted_wf)
