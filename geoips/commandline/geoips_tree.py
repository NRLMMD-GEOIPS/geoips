"""GeoIPS CLI "tree" command.

Single 'geoips tree' command which will display GeoIPS CLI commands up to a --max_depth
value.
"""

from colorama import Fore, Style

from geoips.commandline.geoips_command import GeoipsExecutableCommand


class GeoipsTree(GeoipsExecutableCommand):
    """Tree Command Class for displaying GeoIPS CLI commands in a tree-like fashion.

    Can be configured to print in a colored fashion, up to a maximum depth, and whether
    or not we want the full command string or just the command name at it's depth.
    """

    name = "tree"
    command_classes = []

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
            self._cmd_line_url = r"https://nrlmmd-geoips.github.io/geoips/userguide/command_line.html"  # NOQA
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
            help="The depth of the command tree to print out.",
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

    def print_tree(self, parser, colored=False, level=0, max_depth=2, short_name=False):
        """Display GeoIPS CLI commands up to 'max_depth' in a tree-like fashion.

        This function is recursively called up to 'max_depth' to generate that tree of
        commands. If wanted, we can color the output of the tree by depth and we can
        also control whether or not we want the full command string or just the command
        name by depth.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            - The parser associated with the command at the current depth.
        colored: bool
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

        if short_name:
            # Just grab the exact name of the command.
            # Ie. 'geoips' or 'config' or 'install'
            cmd_txt = f"{split_cmd[-1]}"
        else:
            cmd_txt = cmd_name

        url = f"{self.cmd_line_url}#{cmd_name.replace(' ', '-')}"
        hyperlink = self.link(url, cmd_txt)

        if colored:
            # print the command tree in a colored fashion
            color = self.level_to_color.get(level, Fore.WHITE)
            print(f"{indent}{color}{hyperlink}{Style.RESET_ALL}")
        else:
            # Otherwise just print the string in a normal fashion
            print(f"{indent}{hyperlink}")

        if (
            hasattr(parser, "_subparsers")
            and parser._subparsers
            and level + 1 <= max_depth
        ):
            # If the parser has subparsers, subparsers is not None, and we're not
            # exceeding the max depth specified, then call print_tree again.
            subparsers_action = parser._subparsers._group_actions[0]
            for choice, subparser in subparsers_action.choices.items():
                self.print_tree(
                    subparser,
                    colored=colored,
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
        if depth < 1:
            raise self.parser.error(
                f"Invalid depth value: {depth}. Must be greater than or equal to 1."
            )
        self.print_tree(
            self.top_level_parser,
            colored=args.color,
            max_depth=depth,
            short_name=args.short_name,
        )
