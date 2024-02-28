"""Implements the GeoIPS Command Line Interface."""

import logging
from argparse import ArgumentParser, ArgumentError
from abc import ABC, abstractmethod

from geoips.commandline.log_setup import setup_logging

LOG = logging.getLogger(__name__)


def log_level(name):
    """Return the actual logging level given its name."""
    try:
        getattr(logging, name.upper())
        return name.upper()
    except AttributeError:
        raise ArgumentError(f"{name} is not an available logging level.")


class GeoipsCommand(ABC):
    """Abstract class for all GeoIPS CLI commands."""

    @property
    @abstractmethod
    def subcommand_name(self):
        """The name of the command.

        This command name is used when adding a command to the CLI. So, if the
        GeoipsCLI class includes a subparser_class whose subcommand_name is
        "list", it will create the "geoips list" subcommand.
        """
        pass

    @property
    @abstractmethod
    def subparser_classes(self):
        """A list of subparsers to attach to a parent parser.

        If None, nothing will happen.

        If set to a list of GeoipsCommand subclasses, will attempt to add those
        as subcommands to the current command's parser.
        """
        pass

    @property
    @abstractmethod
    def description(self):
        """A description of the command to be displayed in the command help."""
        pass

    # @property
    # @abstractmethod
    # def help(self):
    #     """A detailed help message for the command."""
    #     pass

    # @property
    # @abstractmethod
    # def formatter_class(self):
    #     """Unsure whether this is needed yet."""
    #     pass

    def __init__(self, parent=None):
        if not parent:
            self.parser = ArgumentParser()
        else:
            if not self.subcommand_name:
                raise AttributeError(
                    "Subparsers must implement the subcommand_name class " "attribute."
                )
            LOG.debug(f"Adding {self.subcommand_name} subcommand.")
            self.parser = parent.subparsers.add_parser(
                self.subcommand_name,
                description=self.description,
                # help=self.help,
                # formatter_class=self.formatter_class
            )
        self.add_arguments()
        self.add_subparsers()

    def add_arguments(self):
        """Override this method to add arguments to a command's parser."""
        pass

    def add_subparsers(self):
        """Add subparsers to the current parser.

        Add each of the GeoipsCommand subclasses listed in
        ``self.subparser_classes`` to the current parser as subparsers.
        """
        if self.subparser_classes:
            self.subparsers = self.parser.add_subparsers()
            for subparser_cls in self.subparser_classes:
                subparser_cls(parent=self)


class GeoipsListSubparser(GeoipsCommand):
    """Base class for subcommands of ``geoips list``."""

    subcommand_name = "list"
    subparser_classes = None
    description = None

    def add_arguments(self):
        """Add arguments common to all subcommands of ``geoips list``."""
        self.parser.add_argument(
            "-p",
            "--plugin-package",
            help=(
                "The name of a package to query. "
                "If not provided, quries all packages."
            ),
        )


class GeoipsListInterfaces(GeoipsListSubparser):
    """Adds the command ``geoips list interfaces``."""

    subcommand_name = "interfaces"
    description = "Retrieve a listing of GeoIPS interfaces and information about them."


class GeoipsListPackages(GeoipsListSubparser):
    """Adds the command ``geoips list packages``."""

    subcommand_name = "packages"
    description = "Retrieve a listing of GeoIPS packages and information about them."

    # def add_arguments():
    #     super().add_arguments()
    #     self.parser.add_arguments('-t', '--temp', help="A dummy argument")


class GeoipsList(GeoipsCommand):
    """Adds the command ``geoips list``."""

    subcommand_name = "list"
    subparser_classes = [GeoipsListInterfaces, GeoipsListPackages]
    description = "Retrieve a list of geoips components"


class GeoipsGet(GeoipsCommand):
    """Adds the command ``geoips get``."""

    subcommand_name = "get"
    subparser_classes = None
    description = (
        "Get detailed information about a GeoIPS component "
        "(e.g. an interface or plugin)"
    )


class GeoipsRun(GeoipsCommand):
    """Adds the command ``geoips run``."""

    subcommand_name = "run"
    subparser_classes = None
    description = "Run GeoIPS"


class GeoipsCLI(GeoipsCommand):
    """Creates the GeoIPS command line interface."""

    subcommand_name = None
    subparser_classes = [GeoipsList, GeoipsGet, GeoipsRun]
    description = "The CLI for GeoIPS"

    def __init__(self):
        self.parser = ArgumentParser()
        self.add_and_handle_logging_arguments()
        self.add_arguments()
        self.add_subparsers()

    def add_and_handle_logging_arguments(self):
        """Add logging arguments and handle them early.

        Add arguments for logging and handle them early so we can use consistent
        logging, even in the rest of the CLI.

        Note, we should not need to do this with anything else. All non-logging related
        top-level arguments should be added via ``add_arguments`` rather than this
        method.
        """
        self.parser.add_argument(
            "-l",
            "--loglevel",
            help="set the log level",
            type=log_level,
        )
        self.parser.add_argument(
            "--short-log-statements",
            help="If set, shorten the prefix to each log message.",
            action="store_true",
        )
        log_args, _ = self.parser.parse_known_args()

        self.LOG = setup_logging(log_args.loglevel, not log_args.short_log_statements)

    def add_arguments(self):
        """Add top-level arguments to the ``geoips`` command."""
        pass


if __name__ == "__main__":
    cli = GeoipsCLI()
    args = cli.parser.parse_args()