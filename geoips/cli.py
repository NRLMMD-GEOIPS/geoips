#!/usr/bin/env python

from inspect import Attribute
import pkgutil
import importlib
from argparse import ArgumentParser, \
                     ArgumentTypeError, \
                     ArgumentDefaultsHelpFormatter, \
                     RawDescriptionHelpFormatter
from geoips import dev, stable, interfaces
from geoips.interfaces.base_interface import BaseInterface
import warnings

# Always actually raise DeprecationWarnings
# Note this SO answer https://stackoverflow.com/a/20960427
warnings.simplefilter('always', DeprecationWarning)

__doc__ = '''
GeoIPS

The Geolocated Information Processing System (GeoIPS) is a generalized
processing system, providing a collection of algorithm and product
implementations facilitating consistent and reliable application of specific
products across a variety of sensors and data types.

GeoIPS acts as a toolbox for internal GeoIPS-based product development - all
modules are expected to have simple inputs and outputs (Python numpy or dask
arrays or xarrays, dictionaries, strings, lists), to enable portability and
simplified interfacing between modules.
'''


class RawDescriptionArgumentDefaultsHelpFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
    '''
    Compound formatter class that preserves the raw description formatting and adds defaults to helps.
    '''
    pass


formclass = RawDescriptionArgumentDefaultsHelpFormatter


def get_interface(name):
    try:
        return getattr(interfaces, name)
    except AttributeError:
        try:
            return getattr(stable, name)
        except AttributeError:
            try:
                return getattr(dev, name)
            except AttributeError:
                raise AttributeError(f'Interface "{name}" not found in either stable or developmental interface sets')


def add_list_interface_parser(subparsers, name, aliases=None):
    # list interpolators
    interface_parser = subparsers.add_parser(
        name,
        aliases=aliases,
        description=f'List available {name}',
        help=f'List available {name}',
        formatter_class=formclass,
        )
    interface_parser.set_defaults(interface=name)
    return interface_parser


def list_dev_interfaces():
    '''
    Return a list of all developmental interfaces
    '''
    return [name for _, name, _ in pkgutil.iter_modules(dev.__path__)]


def list_stable_interfaces():
    '''
    Return a list of all stable interfaces
    '''
    # print(stable.__path__)
    # print([k for k in pkgutil.iter_modules(stable.__path__)])
    return [name for _, name, _ in pkgutil.iter_modules(stable.__path__)]


def print_interfaces(dev=False):
    print('New-Style Interfaces')
    print('--------------------')
    for attr in dir(interfaces):
        attr_val = getattr(interfaces, attr)
        if issubclass(attr_val.__class__, BaseInterface):
            print(attr_val.name)

    print('')
    print('Stable Interfaces')
    print('-----------------')
    for name in list_stable_interfaces():
        print(name)

    print('')
    print('Developmental Interfaces')
    print('------------------------')
    for name in list_dev_interfaces():
        print(name)

    
def print_interface_list(inter):
    mod_list = inter.get_list(by_family=False)

    # Determine column widths for output
    ncol = len(mod_list[0])
    headings = ['name', 'type', 'description']
    if ncol != len(headings):
        raise ValueError('Number of columns does not match the number of headings')
    col_widths = [len(head) for head in headings]
    for mod in mod_list:
        for col in range(len(mod)):
            col_widths[col] = max(col_widths[col], len(mod[col]))
    # col_widths = [wid + 1 for wid in col_widths]
    print(col_widths)

    # Create and print the header
    head_vals = []
    for head_val, width in zip(headings, col_widths):
        head_vals.append(f'{head_val:{width}}')
    head_str = ' | '.join(head_vals)
    print(head_str)
    print(len(head_str) * '-')

    # Create and print the rows
    for mod in mod_list:
        mod_vals = []
        for mod_val, width in zip(mod, col_widths):
            mod_vals.append(f'{mod_val:{width}}')
        mod_str = ' | '.join(mod_vals)
        print(mod_str)


def main():
    parser = ArgumentParser(description=__doc__, formatter_class=formclass)
    subparsers = parser.add_subparsers(title='Commands', description='GeoIPS commands', dest='cmd')

    # run command
    run_parser = subparsers.add_parser(
        'run',
        description='Run a GeoIPS procflow',
        help='Run a GeoIPS procflow',
        formatter_class=formclass,
        )
    run_parser.add_argument('test')
    
    # list command
    list_parser = subparsers.add_parser(
        'list',
        description='List available interfaces',
        help='List available interfaces',
        formatter_class=formclass,
        )
    
    # Don't use `dest` here. It doesn't work well with aliases
    # Instead use `set_defaults` on each parser like below
    # See here for more info:
    #    https://bugs.python.org/issue36664
    list_subparsers = list_parser.add_subparsers()
    
    # list interfaces 
    add_list_interface_parser(list_subparsers, 'interfaces', aliases=['int', 'ints'])
    
    # list plugins for each interface
    add_list_interface_parser(list_subparsers, 'algorithms', aliases=['alg', 'algs'])
    # add_list_interface_parser(list_subparsers, 'boundaries', aliases=['bound', 'bounds'])
    add_list_interface_parser(list_subparsers, 'colormaps', aliases=['cmap', 'cmaps'])
    add_list_interface_parser(list_subparsers, 'filename_formatters', aliases=['ff', 'ffs'])
    # add_list_interface_parser(list_subparsers, 'gridline_formatters', aliases=['gf', 'gfs'])
    add_list_interface_parser(list_subparsers, 'interpolators', aliases=['interp', 'interps'])
    # add_list_interface_parser(list_subparsers, 'outputter_configs', aliases=['oc', 'ocs'])
    add_list_interface_parser(list_subparsers, 'outputters', aliases=['out', 'outs'])
    add_list_interface_parser(list_subparsers, 'procflows', aliases=['pf', 'pfs'])
    # add_list_interface_parser(list_subparsers, 'products', aliases=['prod', 'prods'])
    add_list_interface_parser(list_subparsers, 'readers', aliases=['reader'])
    add_list_interface_parser(list_subparsers, 'title_formatters', aliases=['tf', 'tfs'])

    args = parser.parse_args()
    print(args)

    if args.cmd == 'list':
        if args.interface == 'interfaces':
            print_interfaces()
        else:
            print(get_interface(args.interface))
            print(get_interface(args.interface).get_list())
            # getattr(interfaces, args.interface).get_list(pretty=True, with_family=True, with_description=True)


if __name__ == "__main__":
    main()