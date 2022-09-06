# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

from warnings import warn
from functools import wraps
import inspect


class deprecated:
    """
    A decorator that deprecates a function.

    When applied to a function, will cause that function to raise a DeprecationWarning when called.
    """
    def __init__(self, replacement=None):
        self.replacement = replacement

    def __call__(self, func):
        func_mod = inspect.getmodule(func).__name__
        func_name = f'{func_mod}.{func.__name__}'
        msg = f'Function "{func_name}" is deprecated and will be removed in a future version.'
        if self.replacement:
            repl_mod = inspect.getmodule(self.replacement).__name__
            repl_name = f'{repl_mod}.{self.replacement.__name__}'
            msg += f' Use "{repl_name}" for the same functionality.'

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        wrapped_func.__doc__ = f'DECPRECATED: {msg}\n\n'
        wrapped_func.__doc__ += self.replacement.__doc__
        return wrapped_func


def developmental(func):
    """
    A decorator that marks an interfaces as developmental.

    When applied to a function, will prepend a "developmental" message to the beginning of that function's docstring.
    """
    func_mod = inspect.getmodule(func).__name__
    func_name = f'{func_mod}.{func.__name__}'
    msg = f'"{func_name}" is currently under development and should be expected to change in the future.\n'
    msg += 'Please provide feedback at https://github.com/NRLMMD-GEOIPS/geoips or geoips@nrlmry.navy.mil.'

    @wraps(func)
    def wrapped_func(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapped_func.__doc__ = f'DEVELOPMENTAL: {msg}\n\n'
    wrapped_func.__doc__ += func.__doc__

    return wrapped_func