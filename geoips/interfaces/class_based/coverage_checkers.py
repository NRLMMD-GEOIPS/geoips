# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Coverage checkers interface class."""

import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseCoverageCheckerPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS coverage_checker plugins."""

    data_tree = False

    def _invoke(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Iterate over ``variables`` when a list is given, then delegate.

        When *kwargs* contains a ``variables`` list (from step
        arguments) the coverage checker is invoked once per entry with
        ``variable_name`` injected.  If ``minimum_coverage`` is also
        present, a ``ValueError`` is raised immediately when any
        variable's coverage falls below the threshold.

        Otherwise delegates to the standard ``_invoke`` without
        alteration.

        Parameters
        ----------
        data : xr.DataTree or xr.Dataset or None
            Upstream data passed into the plugin.
        args : tuple
            Additional positional arguments forwarded to the base
            ``_invoke``.
        _obp_initiated : bool, default=False
            Whether the call originates from the Order-Based Procflow.
        kwargs : dict
            Step arguments.  When ``variables`` is a ``list`` it is
            consumed along with ``minimum_coverage``; remaining keys
            are forwarded to each per-variable call.

        Returns
        -------
        DataTreeDitto
            The output of the worst-coverage variable.

        Raises
        ------
        ValueError
            When ``minimum_coverage`` is set and any variable's
            coverage percentage falls below it.
        """
        variables = kwargs.get("variables")
        if not _obp_initiated or not isinstance(variables, list):
            return super()._invoke(data, *args, _obp_initiated=_obp_initiated, **kwargs)

        minimum_coverage = kwargs.pop("minimum_coverage", 0.0)
        kwargs.pop("variables")

        min_cov = 100.0
        result = None
        for vname in variables:
            vkwargs = {**kwargs, "variable_name": vname}
            res = super()._invoke(data, *args, _obp_initiated=_obp_initiated, **vkwargs)
            cov = res.ds.attrs.get("coverage", res.ds.attrs.get("value", 0.0))
            if cov < minimum_coverage:
                raise ValueError(
                    f"Coverage for variable '{vname}' is {cov:.1f}%, "
                    f"below the required minimum of "
                    f"{minimum_coverage:.1f}%."
                )
            if cov < min_cov:
                min_cov = cov
                result = res
        return result

    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        r"""Normalize upstream ``DataTreeDitto`` input into a mutable ``xr.Dataset``.

        Mirrors ``BaseAlgorithmPlugin._pre_call`` by converting upstream
        ``DataTreeDitto`` inputs into a writable ``xr.Dataset`` so ``call()``
        receives the expected input type.

        Non-OBP paths and non-``DataTreeDitto`` inputs pass through unchanged.

        Parameters
        ----------
        data : DataTreeDitto | xr.DataTree | xr.Dataset | None, optional
            Upstream input passed into the algorithm. When the runtime procflow in OBP,
            this will be ``DataTreeDitto`` containing one or more dependency nodes.
        \*args : tuple
            Additional positional arguments forwarded to the base ``_pre_call``.
        _obp_initiated : bool, default=False
            Indicates whether the call originated from the OBP workflow. When
            ``True``, ``DataTreeDitto`` inputs are converted into mutable datasets.
        \*\*kwargs : dict
            Additional keyword arguments forwarded to the base ``_pre_call``.

        Returns
        -------
        xr.Dataset | Any
            A mutable ``xr.Dataset`` when upstream input is normalized from
            ``DataTree``; otherwise whatever the base ``_pre_call`` returns.
        """
        if _obp_initiated and isinstance(data, xr.DataTree):
            data = self._to_mutable_dataset(data)
        return super()._pre_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)

    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        r"""Normalize coverage_checker output into ``DataTreeDitto``.

        The base ``_post_call`` wraps scalar outputs into ``DataTreeDitto`` and stores
        them under ``attrs["value"]``. This override renames that key to
        ``attrs["coverage"]`` so downstream steps can access coverage metadata
        unambiguously.

        Parameters
        ----------
        data : float | Any, optional
            Coverage output produced by the plugin. Scalar values are wrapped by the
            base ``_post_call`` into ``DataTreeDitto``.
        \*args : tuple
            Additional positional arguments forwarded to the base ``_post_call``.
        _obp_initiated : bool, default=False
            Indicates whether the call originated from the OBP workflow. When
            ``True``, wrapped scalar metadata is normalized to use ``coverage``.
        \*\*kwargs : dict
            Additional keyword arguments forwarded to the base ``_post_call``.

        Returns
        -------
        DataTreeDitto | Any
            The normalized ``DataTreeDitto`` output with coverage stored in
            ``data.ds.attrs["coverage"]``; otherwise the result returned by the
            base ``_post_call``.
        """
        # Calling super()._post_call() here results in a DataTreeDitto object. The DTD
        # object will have the same name as the calling CoverageChecker. It will contain
        # a single attribute named "value" that will contain the coverage percentage.
        #
        # The code below will rename the "value" attribute to "coverage".
        data = super()._post_call(data, *args, _obp_initiated=_obp_initiated, **kwargs)
        if _obp_initiated and hasattr(data, "ds") and data.ds is not None:
            attrs = data.ds.attrs
            if "value" in attrs and "coverage" not in attrs:
                attrs["coverage"] = attrs.pop("value")
        return data


class CoverageCheckersInterface(BaseClassInterface):
    """Interpolation routine to apply when reprojecting data."""

    name = "coverage_checkers"
    plugin_class = BaseCoverageCheckerPlugin

    required_args = {"standard": ["xarray_obj", "variable_name"]}
    required_kwargs = {"standard": {}}
    allowable_kwargs = {
        "standard": {
            "area_def",
            "radius_km",
        }
    }

    def get_plugin_for_product(self, product, checker_field="coverage_checker"):
        """Get plugin for product."""
        if checker_field in product:
            self.get_plugin(product[checker_field]["name"])
        else:
            self.get_plugin("masked_array")


coverage_checkers = CoverageCheckersInterface()
