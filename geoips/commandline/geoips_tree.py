# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS CLI "tree" command.

Single 'geoips tree' command which will display GeoIPS CLI commands up to a --max-depth
value.
"""

# :cspell: ignore gpaths

from colorama import Fore, Style

from geoips.commandline.geoips_command import GeoipsExecutableCommand
from geoips.filenames.base_paths import PATHS as gpaths


class GeoipsTree(GeoipsExecutableCommand):
    """Tree Command Class for displaying GeoIPS CLI commands in a tree-like fashion.

    Can be configured to print in a colored fashion, up to a maximum depth, and whether
    or not we want the full command string or just the command name at it's depth.

    Where depth denotes the level of the command you'd like to display.
    I.e. <0> geoips <1> list <2> scripts
    """

    name = "tree"
    command_classes = []

    describe_sectors_outputted = False
    list_sectors_outputted = False

    @property
    def cmd_aliases(self):
        """List of aliases we don't want to include in the tree.

        Without this attribute there will be an entry for each alias of a command name.
        So for 'list' (or 'ls'), there will be two 'geoips list' entries which we don't
        want.
        """
        if not hasattr(self, "_cmd_aliases"):
            self._cmd_aliases = []
            for cmd_name in self.alias_mapping:
                for alias in self.alias_mapping[cmd_name]:
                    # Aliases below are names of actual commands and we need to deal
                    # with this using conditionals in 'print_tree'
                    if alias not in ["sector"]:
                        self._cmd_aliases.append(alias)
        return self._cmd_aliases

    @property
    def top_level_parser(self):
        """The parser associated with the top level 'geoips' command."""
        if not hasattr(self, "_top_level_parser"):
            # Get 'geoips' parser
            self._top_level_parser = self.parent.parser
        return self._top_level_parser

    @property
    def level_to_color(self):
        """A color-mapping dictionary based on the depth of the command tree."""
        if not hasattr(self, "_level_to_color"):
            self._level_to_color = {
                0: Fore.RED,
                1: Fore.YELLOW,
                2: Fore.BLUE,
                3: Fore.MAGENTA,
            }
        return self._level_to_color

    @property
    def cmd_line_url(self):
        """The url to the GeoIPS documentation for the GeoIPS CLI."""
        if not hasattr(self, "_cmd_line_url"):
            self._cmd_line_url = (
                f"{gpaths['GEOIPS_DOCS_URL']}{r'userguide/command_line.html'}"
            )
        return self._cmd_line_url

    def link(self, uri, label=None):
        """Hyperlink the provided uri alongside 'label' if applicable.

        If label is not provided, just return a hyperlink with 'url' as it's text.

        Parameters
        ----------
        uri: str
            - The uniform resource identifier which maps to a certain webpage.
        label: str (default = None)
            - Optional text to hyperlink to.

        Returns
        -------
        hyperlink: str
            - Text that has been hyperlinked to 'uri'
        """
        if label is None:
            label = uri

        parameters = ""
        # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
        escape_mask = "\033]8;{};{}\033\\{}\033]8;;\033\\"
        hyperlink = escape_mask.format(parameters, uri, label)

        return hyperlink

    def add_arguments(self):
        """Add arguments to the tree-subparser for the Tree Command."""
        self.parser.add_argument(
            "--max-depth",
            default=2,
            type=int,
            help=(
                "The depth of the command tree to print out."
                "Where depth denotes the level of the command you'd like to display."
                "\nI.e. <0> geoips <1> list <2> scripts"
            ),
        )
        self.parser.add_argument(
            "--color",
            default=False,
            action="store_true",
            help="Whether or not we want to print the tree in a colored fashion.",
        )
        self.parser.add_argument(
            "--short-name",
            default=False,
            action="store_true",
            help=(
                "Whether or not we want to print the tree as short names or full names."
                "\nFull names are 'geoips -> geoips config -> geoips config install'."
                "\nShort names are 'geoips -> config -> install'."
            ),
        )

    def print_tree(self, parser, color=False, level=0, max_depth=2, short_name=False):
        """Display GeoIPS CLI commands up to 'max_depth' in a tree-like fashion.

        This function is recursively called up to 'max_depth' to generate that tree of
        commands. If wanted, we can color the output of the tree by depth and we can
        also control whether or not we want the full command string or just the command
        name by depth.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            - The parser associated with the command at the current depth.
        color: bool
            - Whether or not we want the output to be colored by depth.
        level: int
            - The current depth of the command tree (starts at 0).
        max_depth: int
            - How deep we would like to expose the command tree
        short_name:
            - Whether or not we want the full command string or just the command name
              at it's depth.
            - Ex: short_name=False -> 'geoips config install'
            - Ex: short_name=True -> 'install'
        """
        indent = " " * (level * 4)
        split_cmd = parser.prog.split()

        if len(split_cmd) <= 2:
            # split_cmd is either ['geoips'] or ['geoips', '<cmd>']
            cmd_name = " ".join(split_cmd)
        else:
            # split_cmd takes the form of the following (same structure for all cmds):
            # ['To', 'use,', 'type', '`geoips', 'config', '<cmd>', '<sub-cmd>', '...`.', 'install'] # NOQA
            # The case above would result in 'geoips config install'
            cmd_name = " ".join(split_cmd[3:5] + [split_cmd[-1]])[1:]

        if (
            cmd_name == "geoips describe sectors" and self.describe_sectors_outputted
        ) or (cmd_name == "geoips list sectors" and self.list_sectors_outputted):
            # Due to how we've structured aliases, these commands need to be manually
            # checked that they've only ran once. This is caused by 'geoips test sector'
            # command, where 'sector is the actual name of a command so we can't include
            # it in the 'cmd_aliases' property of this class.
            return

        if short_name:
            # Just grab the exact name of the command.
            # Ie. 'geoips' or 'config' or 'install'
            cmd_txt = f"{split_cmd[-1]}"
        else:
            cmd_txt = cmd_name

        # Commenting these portions out until we can get the documentation build and
        # make this easily testable. The introduction of Class Factories for commands
        # has made this much harder to implement.

        # url = f"{self.cmd_line_url}#{cmd_name.replace(' ', '-')}"
        # hyperlink = self.link(url, cmd_txt)
        hyperlink = cmd_txt

        if color and not gpaths["NO_COLOR"]:
            # print the command tree in a colored fashion
            color = self.level_to_color.get(level, Fore.WHITE)
            print(f"{indent}{color}{hyperlink}{Style.RESET_ALL}")
        else:
            # Otherwise just print the string in a normal fashion
            print(f"{indent}{hyperlink}")

        if cmd_name == "geoips describe sectors":
            self.describe_sectors_outputted = True
        elif cmd_name == "geoips list sectors":
            self.list_sectors_outputted = True

        if (
            hasattr(parser, "_subparsers")
            and parser._subparsers
            and level + 1 <= max_depth
        ):
            # If the parser has subparsers, subparsers is not None, and we're not
            # exceeding the max depth specified, then call print_tree again.
            subparsers_action = parser._subparsers._group_actions[0]
            for choice, subparser in subparsers_action.choices.items():
                if choice not in self.cmd_aliases:
                    self.print_tree(
                        subparser,
                        color=color,
                        level=level + 1,
                        max_depth=max_depth,
                        short_name=short_name,
                    )

    def __call__(self, args):
        """Run the `geoips tree <opt_args>` command.

        Parameters
        ----------
        args: Namespace()
            - The argument namespace to parse through
        """
        print()
        depth = args.max_depth
        if depth < 0:
            raise self.parser.error(
                f"Invalid depth value: {depth}. Must be greater than or equal to 0."
            )
        self.print_tree(
            self.top_level_parser,
            color=args.color,
            max_depth=depth,
            short_name=args.short_name,
        )
