#!/usr/bin/env python

import pkgutil
import importlib
from argparse import ArgumentParser, \
                     ArgumentTypeError, \
                     ArgumentDefaultsHelpFormatter, \
                     RawDescriptionHelpFormatter
from geoips import dev, stable
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


def import_interface(name):
    try:
        return importlib.import_module(f'geoips.stable.{name}')
    except ModuleNotFoundError:
        try:
            return importlib.import_module(f'geoips.dev.{name}')
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module "{name}" not found in either stable or developmental interface sets')


def list_dev_interfaces():
    '''
    Return a list of all developmental interfaces
    '''
    return [name for _, name, _ in pkgutil.iter_modules(dev.__path__)]


def list_stable_interfaces():
    '''
    Return a list of all stable interfaces
    '''
    print(stable.__path__)
    print([k for k in pkgutil.iter_modules(stable.__path__)])
    return [name for _, name, _ in pkgutil.iter_modules(stable.__path__)]


def print_interfaces(dev=False):
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
    mod_list = inter.get_list(by_type=False)

    # Determine column widths for output
    ncol = len(mod_list[0])
    col_widths = ncol * [0]
    for mod in mod_list:
        for col in range(len(mod)):
            col_widths[col] = max(col_widths[col], len(mod[col]))
    # col_widths = [wid + 1 for wid in col_widths]
    print(col_widths)

    # Create and print the header
    head = ['name', 'type', 'description']
    head_vals = []
    for head_val, width in zip(head, col_widths):
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
    formclass = RawDescriptionArgumentDefaultsHelpFormatter
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
    list_inter_parser = list_subparsers.add_parser(
        'interfaces',
        aliases=['int', 'inter'],
        description='List of GeoIPS interfaces',
        help='List of GeoIPS interfaces',
        formatter_class=formclass,
        )
    list_inter_parser.set_defaults(interface='interfaces')

    # list algorithms
    list_alg_parser = list_subparsers.add_parser(
        'algorithms',
        aliases=['alg', 'algs'],
        description='List of available algorithms',
        help='List of available algorithms',
        formatter_class=formclass,
        )
    list_alg_parser.set_defaults(interface='alg')

    args = parser.parse_args()
    # print(args)

    if args.cmd == 'list':
        if args.interface == 'interfaces':
            print_interfaces()
        else:
            print_interface_list(import_interface(args.interface))


if __name__ == "__main__":
    main()