# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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
import logging

import xarray as xr

from geoips import interfaces
from geoips.utils.types.datatree_ditto import DataTreeDitto
from geoips.utils.types.obp_conduits import OBP_CONDUITS

LOG = logging.getLogger(__name__)

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


# The OBP conduit binding registry and its extractor helpers now live in
# ``geoips.utils.types.obp_conduits`` (imported above as ``OBP_CONDUITS``) so
# that there is a single home for per-kind input wiring.


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
    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Preprocess the data before calling the main plugin method.

        For legacy plugins (``data_tree=False`` with a ``family``) this hook:

        1. Unwraps a ``DataTreeDitto`` (or plain ``DataTree``) input
           to recover the native object via ``_unwrap()``.
        2. Applies a family-specific input conversion if the plugin's
           class defines a ``_family_conversion_map``.

        Datatree-native plugins (``data_tree=True``) pass through
        unchanged.

        Parameters
        ----------
        data : R, optional
            The input data for the plugin.
        _obp_initiated : bool, optional
            Whether or not this plugin is being called via the order
            based procflow.  Defaults to False.

        Returns
        -------
        The processed data.
        """
        if data is None or getattr(self, "data_tree", False):
            return data

        # Step 1: Unwrap DataTree → native type
        data = self._unwrap(data)

        # Step 2: Apply family-specific input conversion (OBP only)
        if _obp_initiated:
            conversion_map = getattr(self, "_family_conversion_map", None)
            if conversion_map is not None:
                spec = conversion_map.get(self.family)
                if spec is not None and spec.input_converter is not None:
                    if spec.input_type is not None and not isinstance(
                        data, spec.input_type
                    ):
                        data = spec.input_converter(data)
                    elif spec.input_type is None:
                        data = spec.input_converter(data)

        return data

    # def _post_call(self, data: R, *args, **kwargs) -> R:
    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Post-process the data after calling the main plugin method.

        For legacy plugins (``data_tree=False`` with a ``family``) this hook:

        1. Applies a family-specific output (reverse) conversion if the
           plugin's class defines a ``_family_conversion_map``.
        2. Wraps a non-DataTree result back into a ``DataTreeDitto``
           via ``_wrap()``.

        Datatree-native plugins (``data_tree=True``) pass through
        unchanged.

        Parameters
        ----------
        data : R, optional
            The output data from the plugin.
        _obp_initiated : bool, optional
            Whether or not this plugin is being called via the order
            based procflow.  Defaults to False.
        _pre_call_attrs : dict or None
            Upstream metadata captured *before* ``_pre_call``
            converted the input.  Re-applied after family output
            conversion so rebuild-from-scratch converters
            (``numpy_to_dataset``, …) do not lose metadata such as
            ``source_name`` or ``start_datetime``.  Injected by
            ``_invoke``.

        Returns
        -------
            The processed data.
        """
        if data is None or getattr(self, "data_tree", False):
            return data

        # Step 1: Apply family-specific reverse conversion (OBP only)
        if _obp_initiated:
            conversion_map = getattr(self, "_family_conversion_map", None)
            if conversion_map is not None:
                spec = conversion_map.get(self.family)
                if spec is not None and spec.output_converter is not None:
                    data = spec.output_converter(data)

        # Step 1b: Propagate upstream metadata into converter-rebuilt output.
        # Converters such as ``numpy_to_dataset`` create fresh objects
        # without upstream attrs — this restores them.
        pre_call_attrs = kwargs.pop("_pre_call_attrs", None)
        if _obp_initiated and pre_call_attrs and hasattr(data, "attrs"):
            for k, v in pre_call_attrs.items():
                data.attrs.setdefault(k, v)

        # Step 2: Wrap into DataTreeDitto if not already (OBP only)
        if _obp_initiated and not isinstance(data, xr.DataTree):
            data = self._wrap(data)

        return data

    def _unwrap(self, data):
        """Unwrap a DataTree-like container to the original type.

        If the input is a ``DataTreeDitto``, call ``get_original()``
        to recover the native object (numpy array, Dataset, dict, …)
        that was originally passed to the constructor.  If the input
        is a plain ``xr.DataTree`` that contains a ``DataTreeDitto``
        dataset, extract and unwrap it.

        For multi-input DataTrees (collected by
        ``Workflow._collect_upstream_data``) the root dataset carries
        no ``_ditto_original_type``.  In that case:

        * A single child is unwrapped directly.
        * Multiple children pass through unchanged (the caller's
          ``_extract_child_kwargs`` handles extraction).

        Parameters
        ----------
        data : Any
            The container passed to the plugin callable.

        Returns
        -------
        Any
            The unwrapped native object.
        """
        if isinstance(data, DataTreeDitto):
            return data.get_original()

        if isinstance(data, xr.DataTree):
            children = dict(data.children)
            if children and not data.ds.attrs.get("_ditto_original_type"):
                if len(children) == 1:
                    child = next(iter(children.values()))
                    if isinstance(child, DataTreeDitto):
                        return child.get_original()
                    return child
                return data
            try:
                return DataTreeDitto(data.ds).get_original()
            except (TypeError, ValueError, RuntimeError) as exc:
                LOG.debug("Could not unwrap DataTree to original: %s", exc)
        return data

    def _wrap(self, result):
        """Wrap a non-DataTree result back into a DataTreeDitto.

        If *result* is already a ``DataTreeDitto`` it is returned as-is.
        Any other non-None value is wrapped into a ``DataTreeDitto``
        (with an automatic name derived from the plugin).

        Parameters
        ----------
        result : Any
            The return value of ``_post_call``.

        Returns
        -------
        DataTreeDitto or the original result.
        """
        if result is None:
            return result
        if isinstance(result, DataTreeDitto):
            return result
        # If we already have a DataTree, convert to DTD and return
        if isinstance(result, xr.DataTree):
            return DataTreeDitto.from_datatree(result)
        # In the case of a scalar, create a DataSet, then convert to DataTreeDitto.
        # The resulting DTD instance will have a single attribute, "value", containing
        # the scalar value. This must be handled by the calling plugin's `_post_call()`
        # to give the attribute an appropriate name. For example, CoverageCheckers
        # rename "value" to "coverage"
        if isinstance(result, (str, int, float, bool)):
            ds = xr.Dataset(attrs={"value": result})
            return DataTreeDitto(ds, name=getattr(self, "name", "result"))
        # For all types not previously handled, convert whatever we got to a DTD whose
        # name is the same as the calling plugin and return
        plugin_name = getattr(self, "name", "result")
        try:
            return DataTreeDitto(result, name=plugin_name)
        except TypeError as exc:
            raise TypeError(
                f"Plugin '{plugin_name}' (kind "
                f"'{getattr(self, 'interface', 'unknown')}') returned a value of "
                f"type '{type(result).__module__}.{type(result).__name__}' that "
                f"could not be wrapped in a DataTreeDitto because no converter is "
                f"registered for it. Either return a supported type (DataTree, "
                f"Dataset, DataArray, ndarray, dict, list, or a scalar) or "
                f"register a converter for this type. See "
                f"geoips.utils.types.converters for examples.\n"
                f"Original error: {exc}"
            ) from exc

    @staticmethod
    def _to_mutable_dataset(data):
        """Convert a DataTree with children into a mutable ``xr.Dataset``.

        ``DataTree.ds`` returns an immutable ``DatasetView``.  Plugins
        that need to write into the dataset must call this helper first.

        * Single child with its own data_vars → ``children[0].to_dataset()``
        * Single child whose data lives in *its* children (reader-style
          multi-dataset output: root is attrs-only, sub-children hold each
          variable group) -> ``xr.merge(sub-children)`` with root attrs preserved
        * Multiple children -> ``xr.merge(...)``
        * Not a DataTree -> returned unchanged.
        """
        # if not isinstance(data, xr.DataTree):
        #     return data
        # children = list(data.children.values())
        # if len(children) == 1:
        #     child = children[0]
        #     child_ds = child.ds
        #     if child_ds is not None and not child_ds.data_vars and child.children:
        #         sub_children = list(child.children.values())
        #         if len(sub_children) == 1:
        #             merged = sub_children[0].to_dataset()
        #         else:
        #             merged = xr.merge([c.to_dataset() for c in sub_children])
        #         for k, v in child_ds.attrs.items():
        #             merged.attrs.setdefault(k, v)
        #         return merged
        #     return child.to_dataset()
        # if len(children) > 1:
        #     return xr.merge([c.to_dataset() for c in children])
        # return data

        if not isinstance(data, xr.DataTree):
            return data

        children = list(data.children.values())

        if not children:
            return data

        if len(children) > 1:
            return xr.merge(child.to_dataset() for child in children)

        child = children[0]
        child_ds = child.ds

        if child_ds is None or child_ds.data_vars or not child.children:
            return child.to_dataset()

        sub_children = list(child.children.values())

        if len(sub_children) == 1:
            data = sub_children[0].to_dataset()
        else:
            data = xr.merge(sub_child.to_dataset() for sub_child in sub_children)

        data.attrs = {**child_ds.attrs, **data.attrs}
        return data

    @staticmethod
    def _extract_child_kwargs(data, kwargs):
        """Inject conduit-mapped keyword arguments from upstream DataTree children.

        Walks each child of *data* (a ``multi_input`` DataTree built by
        ``_collect_upstream_data``), reads ``plugin_kind`` from attrs,
        looks up the matching conduit in ``OBP_CONDUITS``, and injects
        the extracted value into *kwargs* when the target key is not
        already present.

        After all conduits have been processed the legacy product-name
        rename bridge is applied (``_apply_legacy_product_name_rename``).

        Parameters
        ----------
        data : xr.DataTree
            The ``multi_input`` DataTree whose children are dependency
            outputs from earlier steps.
        kwargs : dict
            Mutable keyword-argument dict (from step arguments).
            Conduit-injected keys are added in-place.

        Returns
        -------
        dict
            The same *kwargs* dict, now including any conduit-injected
            values.
        """
        if not isinstance(data, xr.DataTree):
            return kwargs

        children = dict(data.children)
        if not children:
            return kwargs

        from geoips.utils.types.obp_conduits import OBP_CONDUITS

        for _child_name, child in children.items():
            pkind = str(child.ds.attrs.get("plugin_kind", "")) if child.ds is not None else ""
            conduit = OBP_CONDUITS.get(pkind)
            if conduit is None:
                continue
            kwarg_name = conduit["kwarg"]
            if kwarg_name in kwargs:
                continue
            val = conduit["extract"](child)
            if val is not None:
                kwargs[kwarg_name] = val

        _apply_legacy_product_name_rename(kwargs)

        return kwargs

    @staticmethod
    def _capture_attrs(data):
        """Return a dict copy of ``data.attrs`` when available, or None.

        Family output converters (e.g. ``numpy_to_dataset``) rebuild an
        object from scratch and lose upstream metadata.  Capturing attrs
        before ``_pre_call`` strips the original input lets
        ``_post_call`` re-apply them after conversion.

        Parameters
        ----------
        data : Any
            The unwrapped-but-not-yet-input-converted upstream payload.

        Returns
        -------
        dict or None
            Shallow copy of ``data.attrs``, or None if *data* has no
            ``attrs`` property.
        """
        if data is None:
            return None
        if hasattr(data, "attrs"):
            attrs = data.attrs
            if isinstance(attrs, dict):
                return dict(attrs)
        return None

    def _normalize_obp_kwargs(self, kwargs):
        """Rename OBP-injected kwarg names for legacy plugins.

        Subclasses override this to translate new-style argument names
        (e.g. ``filenames``, ``output_filenames``) back to the names
        legacy (family-bearing) plugins expect (e.g. ``fnames``,
        ``output_fnames``).  Called after ``_pre_call`` and before
        ``_call_kwargs``, so the renamed kwargs survive the
        ``_obp_filter_kwargs`` filter.

        The default implementation returns *kwargs* unchanged.

        Returns
        -------
        dict
            The (possibly-renamed) kwargs dictionary.
        """
        return kwargs

    def _normalize_call_args(self, data, args, kwargs, *, _obp_initiated=False):
        """Normalize raw ``__call__`` arguments before preprocessing.

        Interface-specific subclasses can override this hook when they need to
        support multiple public calling conventions while preserving one
        internal convention for ``_pre_call`` and ``call``.
        """
        return data, args, kwargs

    def _invoke(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Call the main plugin method.

        Additionally, filter out unaccepted arguments if initiated via the OBP.
        Unwrap / wrap and family-specific type conversions are handled by
        ``_pre_call()`` and ``_post_call()``.

        Parameters
        ----------
        data : R, optional
            The output data from the plugin.
        _obp_initiated : bool, optional
            Whether or not this plugin is being called via the order based procflow.
            Defaults to False.

        Returns
        -------
            The processed data.
        """
        new_kwargs = kwargs
        data, args, new_kwargs = self._normalize_call_args(
            data, args, new_kwargs, _obp_initiated=_obp_initiated
        )

        if data is None:
            if _obp_initiated:
                new_kwargs = self._normalize_obp_kwargs(new_kwargs)
            # No upstream data (e.g. a reader called outside OBP, or a
            # metadata-only read).  ``_call_kwargs`` also runs
            # ``_obp_filter_kwargs`` when ``_obp_initiated`` is true.
            # ``_pre_call`` is a no-op for ``data is None``.
            call_kwargs = self._call_kwargs(new_kwargs, _obp_initiated)
            result = self.call(*args, **call_kwargs)
            return self._post_call(
                result, *args, _obp_initiated=_obp_initiated, **new_kwargs
            )

        if _obp_initiated:
            new_kwargs = self._extract_child_kwargs(data, new_kwargs)

        pre_call_attrs = self._capture_attrs(self._unwrap(data))
        data = self._pre_call(data, *args, _obp_initiated=_obp_initiated, **new_kwargs)

        if _obp_initiated:
            new_kwargs = self._normalize_obp_kwargs(new_kwargs)

        if data is None:
            call_kwargs = self._call_kwargs(new_kwargs, _obp_initiated)
            result = self.call(*args, **call_kwargs)
            return self._post_call(
                result,
                *args,
                _obp_initiated=_obp_initiated,
                _pre_call_attrs=pre_call_attrs,
                **new_kwargs,
            )

        # Note: ``_call_kwargs`` drops conduit-injected kwargs (e.g.
        # ``xarray_obj``) the plugin's ``call`` does not accept. In the unpacking
        # branch it must be computed *after* ``_kwarg_to_positional`` (which pops
        # the promoted keys from ``new_kwargs`` in-place), so those keys are not
        # passed both positionally and by keyword.
        if self._use_positional_unpacking(data, _obp_initiated):
            new_args = _kwarg_to_positional(new_kwargs, self.call)
            call_kwargs = self._call_kwargs(new_kwargs, _obp_initiated)
            result = self.call(*new_args, **call_kwargs)
        else:
            call_kwargs = self._call_kwargs(new_kwargs, _obp_initiated)
            if _obp_initiated and not self._should_pass_positional_data(call_kwargs):
                # ``call`` has no free positional slot for the injected tree — its
                # real input arrives via a kwarg (e.g. a colormapper's
                # ``data_range``, a reader's ``filenames``, a conduit-injected
                # ``xarray_obj``), or the signature is keyword-only. Dropping the
                # positional ``data`` lets an entry step's injected tree
                # (including a top-level "empty dataset") reach such plugins
                # harmlessly instead of raising "multiple values"/"takes 0
                # positional arguments".
                result = self.call(*args, **call_kwargs)
            else:
                # ``data`` is passed positionally; for legacy families the same
                # data has already been converted into ``data`` by ``_pre_call``.
                result = self.call(data, *args, **call_kwargs)

        data = self._post_call(
            result,
            *args,
            _obp_initiated=_obp_initiated,
            _pre_call_attrs=pre_call_attrs,
            **new_kwargs,
        )
        return data

    def _should_pass_positional_data(self, call_kwargs):
        """Return True if injected ``data`` should be passed to ``call`` positionally.

        ``self.call`` is a bound method, so ``inspect.signature`` already drops
        ``self``. Data is passed positionally only when ``call`` actually has a
        free positional slot for it:

        * If ``call`` leads with a positional parameter
          (``POSITIONAL_ONLY``/``POSITIONAL_OR_KEYWORD``), pass data there —
          unless that same name is already supplied via ``call_kwargs`` (e.g. a
          colormapper's ``data_range`` or a reader's ``filenames``), which would
          raise "multiple values for argument ...".
        * Otherwise, pass positionally only if ``call`` accepts ``*args``
          (``VAR_POSITIONAL``) to absorb it.
        * A keyword-only-leading signature (``def call(self, *, x=...)``) or one
          with no parameters has no positional slot, so data is dropped rather
          than forced in (which would raise ``TypeError``).
        """
        leading = None
        has_var_positional = False
        for name, p in inspect.signature(self.call).parameters.items():
            if p.kind is inspect.Parameter.VAR_POSITIONAL:
                has_var_positional = True
            elif leading is None and p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                leading = name
        if leading is not None:
            return leading not in call_kwargs
        return has_var_positional

    @staticmethod
    def _use_positional_unpacking(data, _obp_initiated):
        """Return True when ``call()`` should receive unpacked positional args.

        Multi-child multi_input DataTrees cannot be passed as the first
        positional ``data`` arg (signature mismatch).  This helper detects
        that case so ``_invoke`` can switch to positional unpacking.
        """
        return (
            _obp_initiated
            and isinstance(data, xr.DataTree)
            and len(dict(data.children)) > 1
            and not data.ds.attrs.get("_ditto_original_type")
        )

    def _obp_filter_kwargs(self, kwargs):
        """Return a dict of only the kwargs accepted by ``self.call``.

        If ``call`` accepts ``**kwargs`` (a ``VAR_KEYWORD`` parameter) every key
        is retained, since such a signature accepts arbitrary keywords.
        """
        params = inspect.signature(self.call).parameters.values()
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params):
            return dict(kwargs)
        accepted = {p.name for p in params}
        result = {k: v for k, v in kwargs.items() if k in accepted}
        return result

    def _call_kwargs(self, kwargs, _obp_initiated):
        """Return the kwargs to forward to ``self.call``.

        Under OBP, filter to only those ``call`` accepts so conduit-injected
        kwargs that don't match this plugin's signature are dropped. Outside
        OBP, pass kwargs through unchanged to preserve legacy behavior.
        """
        return self._obp_filter_kwargs(kwargs) if _obp_initiated else kwargs

    def __init__(self, module=None):
        """
        Initialize the plugin object inheriting from BaseClasePlugin.

        Parameters
        ----------
        module: ModuleType, default=None
            The module from which the class-based plugin originated. This is used to
            collect metadata from the module and attach it to the plugin object. The
            metadata can then be used during validation to indicate where failing
            plugins originated. If None, the 'testing' attributes will be set to a
            string value that can also be used in tests.
        """
        if module:
            self.module_name = module.__name__
            self.module_path = module.__file__
        else:
            self.module_name = "Unknown."
            self.module_path = "Unknown."

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

        call_signature = inspect.signature(call_method)
        self_param = inspect.Parameter(
            "self",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        call_params = [
            p for p in call_signature.parameters.values() if p.name != "self"
        ]
        _call.__signature__ = call_signature.replace(
            parameters=[self_param] + call_params
        )
        _call.__annotations__ = getattr(call_method, "__annotations__", {})
        cls.__call__ = _call


def _kwarg_to_positional(kwargs, call_func):
    """Convert kwargs to positional args matching ``call_func`` signature.

    For multi-child multi_input DataTrees, ``_invoke`` cannot pass the
    DataTree as the first positional arg (signature mismatch).  This
    helper inspects ``call_func``'s parameter names and promotes
    matching kwargs to positional arguments.

    Parameters
    ----------
    kwargs : dict
        Keyword arguments (mutated in-place — matching keys are popped).
    call_func : callable
        The plugin's ``call`` method (used for signature inspection).

    Returns
    -------
    tuple
        Positional arguments for ``call_func``.
    """
    sig = inspect.signature(call_func)
    positional = []
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        if param.kind not in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            break
        if pname in kwargs:
            positional.append(kwargs.pop(pname))
        elif param.default is not inspect.Parameter.empty:
            positional.append(param.default)
        elif _resolve_positional_alias(pname, kwargs, positional):
            pass
        elif pname in _PARAM_DEFAULTS:
            positional.append(_PARAM_DEFAULTS[pname])
        else:
            raise TypeError(
                f"_kwarg_to_positional: required parameter {pname!r} "
                f"is missing from kwargs and cannot be filled automatically. "
                f"Available kwargs: {list(kwargs)}"
            )
    return tuple(positional)


#: Positional-parameter names that have no meaningful kwarg counterpart in
#: the OBP conduit system but are safe to default to ``None`` (the plugin
#: creates its own internally — e.g. ``output_xarray`` in interpolators).
_PARAM_DEFAULTS: dict[str, object] = {
    "output_xarray": None,
}

#: Legacy SSP plugins call the same upstream value by different parameter
#: names.  This maps a ``call`` signature's positional parameter name to
#: the bespoke conduit kwarg name that carries the actual value.
_CALL_TO_CONDUIT_ALIASES: dict[str, tuple[str, ...]] = {
    "data": ("xarray_obj",),
    "input_xarray": ("xarray_obj",),
    "xobj": ("xarray_obj",),
}


def _resolve_positional_alias(pname, kwargs, positional):
    """Try to fill *pname* from a conduit-kwarg alias.

    Returns True if a matching alias was found and consumed, False otherwise.
    """
    for alias in _CALL_TO_CONDUIT_ALIASES.get(pname, ()):
        if alias in kwargs:
            positional.append(kwargs.pop(alias))
            return True
    return False


def _apply_legacy_product_name_rename(kwargs):
    """Rename the first data variable to ``product_name`` value for legacy SSP.

    Some legacy algorithms produce a dataset whose first data variable
    has a generic name (e.g. the first channel name). Downstream legacy
    plugins (filename formatters, output formatters) expect the variable
    to be named after the product. When both ``xarray_obj`` and
    ``product_name`` are present in *kwargs* and the target name does not
    already exist as a variable or coordinate, the first data variable is
    renamed in-place.

    This is a backwards-compatibility bridge for legacy
    single-source-procflow plugins and only fires when both keyword
    arguments appear together via the conduit system.
    """
    xo = kwargs.get("xarray_obj")
    pn = kwargs.get("product_name")
    if xo is None or pn is None:
        return
    if not (hasattr(xo, "data_vars") and xo.data_vars):
        return
    if not isinstance(pn, str):
        return
    if pn in xo.data_vars:
        return
    first_var = list(xo.data_vars)[0]
    if first_var != pn and pn not in xo:
        kwargs["xarray_obj"] = xo.rename({first_var: pn})
