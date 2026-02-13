"""Implements a base class for class-based plugins.

The base class implemented here would expose the call signature of the child plugin
class as `__call__()` while also providing hooks for pre- and post-processing.

The hooks are available as `_pre_call()` and `_post_call()`. They should be used to
implement common functionality that all plugins of this type should posess but which we
don't want developers to need to implement. They are intended to be overridden by the
child plugin-type class (e.g. BaseReaderPlugin). They should define what kwargs they
accept when defined on the plugin-type class but should accept their arguments from
`**kwargs` from `__call__()`.

The `call()` method should be overridden on the actual plugin class. It should provide
the data processing for the plugin. `__call__()`'s signature will be identical to that
of `call()` except that `call()` should not accept `**kwargs`. That should be consumed
by the hooks.

`__call__()` should not be overridden anywhere.

I removed this for now, but maybe consider again later:
I still need to do more research to understand the effects of ParamSpec, TypeVar, and
Generic, but they are supposed to help make this class and its children interact with
IDE, static analysis tools, and other type checkers correctly.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import functools
import inspect

from geoips import interfaces

# P = ParamSpec("P")
# R = TypeVar("R")


# To do:
# - __repr__()
# - __str__()
# - tokenize() - Call from _post_call if tokenize=True
# - Converter to/from dict of xarray - Probably pure, accept data and family name
# - Converter to/from data_tree


def valid_str_attr(cls, attr_name: str):
    """Check that the given attribute is a non-empty string."""
    attr_value = getattr(cls, attr_name, None)
    if not isinstance(attr_value, str):
        raise TypeError(f"{cls.__name__}.{attr_name} must be a string")
    if not attr_value:
        raise ValueError(f"{cls.__name__}.{attr_name} cannot be empty")


# class BaseClassPlugin(Generic[P, R], ABC):
class BaseClassPlugin(ABC):
    """The base class for GeoIPS class-based plugins.

    All plugins are required to carry the following class attributes:

    - interface: The interface type the plugin belongs to (e.g. 'readers', 'products').
      This is typically provided by the interface-level plugin class and not the
      individual plugin class.
    - family: The family name of the plugin. This should be defined by the plugin class.
    - name: The specific name of the plugin. This should be defined by the plugin class.

    Subclasses of this base class must also implement the following methods:

    - call(): The main method that performs the plugin's functionality. This method
      should be implemented by the plugin class.
    - _pre_call(): A hook method that can be overridden to preprocess data before
      calling the main call() method. This method should accept the same arguments as
      call() via `*args` and `**kwargs` and should, typically, be implemented by the
      interface-level plugin class.
    - _post_call(): A hook method that can be overridden to post-process data after
      calling the main call() method. This method should accept the same arguments as
      call() via `*args` and `**kwargs` and should, typically, be implemented by the
      interface-level plugin class.

    The purpose of `_pre_call()` and `_post_call()` is to allow for common
    functionality that all plugins of a certain type should possess, without requiring
    developers to implement this functionality in every plugin class. Initially, this
    will be used to convert inputs from DataTree to other formats and back to DataTree
    after processing, but it could be used for other common tasks as well.
    """

    # If set to True, we are in OBP. False means we are in a legacy procflow.
    # Set up logic in this or interface classes to convert from DT to data type
    # referenced in family

    # If no family is provided, just assume it works with DT
    data_tree = False
    required_attributes = ["interface", "family", "name"]

    def _check_interface_attribute(cls):
        """Check the validity of the 'interface' attribute.

        Checks to be sure that the interface attribute is a non-empty string and that it
        is a known plugin interface.
        """
        valid_str_attr(cls, "interface")
        if cls.interface not in interfaces.list_available_interfaces()["class_based"]:
            raise ValueError(
                f"{cls.__name__}.interface '{cls.interface}' is not a known plugin "
                "interface"
            )

    def _check_family_attribute(cls):
        """Check the validity of the 'family' attribute."""
        valid_str_attr(cls, "family")

    def _check_name_attribute(cls):
        """Check the validity of the 'name' attribute."""
        valid_str_attr(cls, "name")

    @abstractmethod
    # def call(self, *args: P.args, **kwargs: P.kwargs) -> R:
    def call(self, *args, **kwargs):
        """Callable method to be implemented by the plugin class."""
        pass

    # hooks are intentionally loose; document their accepted kwargs
    # def _pre_call(self, data: R, *args, **kwargs) -> R:
    def _pre_call(self, data=None, *args, **kwargs):
        """Preprocess the data before calling the main plugin method.

        Parameters
        ----------
        data : The input data for the plugin.

        Returns
        -------
        The processed data.
        """
        return data

    # def _post_call(self, data: R, *args, **kwargs) -> R:
    def _post_call(self, data=None, *args, **kwargs):
        """Post-process the data after calling the main plugin method.

        Parameters
        ----------
        data : R
            The output data from the plugin.

        Returns
        -------
            The processed data.
        """
        return data

    # def _invoke(self, data: R, *args: P.args, **kwargs: P.kwargs) -> R:
    def _invoke(self, data=None, *args, **kwargs):
        # In the long run every plugin will accept a data tree
        # (I.e. colormapper modifies metadata)
        # if self.interface in [
        #     "colormappers",
        #     "sector_spec_generators",
        #     # "sector_metadata_generators",
        # ]:
        if data is None:
            data = self.call(*args, **kwargs)
        else:
            data = self._pre_call(data, *args, **kwargs)
            data = self.call(data, *args, **kwargs)
            data = self._post_call(data, *args, **kwargs)
        return data

    def __init__(self, module=None):
        """
        Initialize the plugin object inheriting from BaseClasePlugin.

        Parameters
        ----------
        module: ModuleType, default=None
            - The module in which the class-based plugin came from. This is used to
              collect metadata from the module and attach it to the plugin object. This
              can then be used when validating plugins to denote where failing plugins
              come from. If None, we will set the 'testing' attributes to a string
              which can be used in tests as well.
        """
        if module:
            self.module_name = module.__name__
            self.module_path = module.__file__
        else:
            self.module_name = "No associated module name."
            self.module_path = "No associated module path."

    def __init_subclass__(cls, *, abstract=False, **kwargs) -> None:
        """
        Initialize a subclass of the plugin.

        Parameters
        ----------
        abstract : bool, optional
            If True, the subclass is treated as abstract. When treated as abstract,
            validation is disabled in __init_subclass__. Defaults to False.

        Raises
        ------
        TypeError
            If the subclass does not define the required attributes.
        TypeError
            If the subclass does not implement the call() method.
        TypeError
            If the subclass overrides the __call__() method.

        Returns
        -------
        None
        """
        super().__init_subclass__(**kwargs)

        # Treat the root as abstract and honor explicit marker
        if cls is BaseClassPlugin or abstract:
            cls.__plugin_abstract__ = True
            return

        # Enforce required attributes and run attribute checkers if they exist
        for attr in cls.required_attributes:
            # Ensure required attributes are defined
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define '{attr}' attribute")

            # Run attribute checker for the current attribute if it exists
            attribute_checker = getattr(cls, f"_check_{attr}_attribute", None)
            if attribute_checker is not None:
                attribute_checker(cls)

        # Prevent overriding __call__ in a True class-based plugin
        if "__call__" in cls.__dict__:
            raise TypeError(f"{cls.__name__} cannot override __call__")

        try:
            call_method = cls.__dict__.get("call")
        except AttributeError:
            raise TypeError(f"{cls.__name__} must implement call()")

        @functools.wraps(call_method)
        def _call(self, data=None, *args, **kwargs):
            return cls._invoke(self, data, *args, **kwargs)

        _call.__signature__ = inspect.signature(call_method)  # mirror only call()
        _call.__annotations__ = getattr(call_method, "__annotations__", {})
        cls.__call__ = _call
