# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Workflow plugin models.

Defines pydantic models related to Workflow plugins,
including top-level callable interfaces (eg. Readers, OutputFormatters, etc.).
"""

# Previously, the model names used as type hints were quoted marking them as strings;
# leading to forward references, which allow referring to a class before Python has
# fully parsed it.

# By adding from __future__ import annotations, Python defers evaluation of all type
# annotations until runtime, automatically treating them as strings. This eliminates
# the need to manually quote forward-referenced types (simplified type hinting).
from __future__ import annotations

# Python Standard Libraries
from copy import deepcopy
import datetime as dt
from glob import glob
import logging
import re
from typing import Any, Dict, List, Literal, Optional, Union

# Third-Party Libraries
from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    FilePath,
    field_validator,
    model_validator,
    ValidationInfo,
)

# GeoIPS imports
from geoips.constants import PLUGIN_PROVIDED
from geoips import interfaces
from geoips.config import config
from geoips.errors import (
    DependencyCycleError,
    PluginResolutionError,
)
from geoips.pydantic_models.v1.bases import (
    PluginModel,
    FrozenModel,
    PermissiveFrozenModel,
    PythonIdentifier,
    StepReference,
)
from geoips.pydantic_models.v1.algorithms import AlgorithmArgumentsModel
from geoips.pydantic_models.v1.coverage_checkers import CoverageCheckerArgumentsModel
from geoips.pydantic_models.v1.filename_formatters import (
    FilenameFormatterArgumentsModel,
)
from geoips.pydantic_models.v1.interpolators import InterpolatorArgumentsModel
from geoips.pydantic_models.v1.output_checkers import OutputCheckerArgumentsModel
from geoips.pydantic_models.v1.readers import ReaderArgumentsModel
from geoips.utils.types.partial_lexeme import Lexeme

LOG = logging.getLogger(__name__)

SCAFFOLD_KINDS = frozenset({"split", "join"})
"""Kinds reserved as scaffolding markers.

Steps with these kinds are accepted by schema validation and executed by
workflow orchestration rather than plugin resolution.
"""

INPUT_REF = "_input"
"""Magic ``depends_on`` token marking a workflow's data-injection entry step.

A step whose ``depends_on`` contains ``_input`` receives the data injected into
the workflow from the outside: the parent's upstream tree for a sub-workflow (or
split branch), or an empty ``DataTree`` for a top-level workflow. It is a virtual
source (not a real step), so it is skipped by dependency-reference validation,
cycle detection, and topological ordering. If no step declares ``_input``, the
first step receives the injected data (backward-compatible fallback).
"""

DEFAULT_RETENTION = "keep_referenced"
"""Default retention policy when ``retention`` is not specified in the YAML."""


ORDERED_PRODUCT_FAMILIES = [
    "algorithm",
    "algorithm_colormapper",
    "algorithm_interpolator_colormapper",
    "interpolator",
    "interpolator_algorithm",
    "interpolator_algorithm_colormapper",
]


def get_plugin_names(plugin_kind: str) -> List[str]:
    """Return valid plugin names for passed plugin kind.

    Parameters
    ----------
    plugin_kind : str
        valid plugin interface name

    Returns
    -------
    list
        A list of plugin names for a valid plugin kind

    Raises
    ------
    AttributeError
        If the plugin kind is invalid

    """
    interface_name = Lexeme(plugin_kind).plural
    try:
        interface = getattr(interfaces, interface_name)
    except AttributeError as e:
        error_message = f"{plugin_kind} is not a recognized plugin kind."
        LOG.critical(error_message, exc_info=True)
        raise AttributeError(error_message) from e

    interface_entry = interface.plugin_registry.registered_plugins[
        interface.interface_type
    ][interface_name]

    if interface_name == "products":
        plugin_names = []
        for source_name in interface_entry:
            for plugin_name in interface_entry[source_name]:
                plugin_names.append((source_name, plugin_name))

        return plugin_names
    else:
        return list(interface_entry.keys())


def get_plugin_kinds() -> set[str]:
    """Return plugin kinds from available interfaces.

    Returns
    -------
    set of str
        singular names of distinct plugin kinds
    """
    return {
        Lexeme(plugin_kinds).singular
        for ifs in interfaces.list_available_interfaces().values()
        for plugin_kinds in ifs
    }


def _product_step_id(name: list[str]) -> str:
    """Build a valid PythonIdentifier step ID from a product name tuple.

    Joins the name segments with ``"_"`` then replaces any remaining
    non-identifier characters with ``"_"``, ensuring the result satisfies
    ``str.isidentifier()``.
    """
    return re.sub(r"[^a-zA-Z0-9_]", "_", "_".join(name))


# NOTE: We need to move all of the argument models to their own module once implemented
# and supported by the OBP. geoips.plugins.modules.procflows.order_based:validate_arguments  # NOQA
# will not work otherwise


class OutputFormatterArgumentsModel(PermissiveFrozenModel):
    """Validate Output Formatter arguments."""

    pass


class AlgorithmStepValidationModel(PermissiveFrozenModel):
    """Validate step-level requirements for algorithm plugins."""

    @model_validator(mode="after")
    def _variables_required_algorithm_plugins(self):
        """
        Validate that ``variables`` field is present when required.

        Ensures that input for the ``variables`` argument is provided for specific
        algorithm plugins and is not None.

        Returns
        -------
        Self
            The validated model instance, ensuring ``variables`` field is not empty.

        Raises
        ------
        ValueError
            If the ``variables`` argument is required but nor provided.
        """
        if self.name in [
            "model_channel",
            "absdiff_mst",
        ] and not self.arguments.get("variables"):
            raise ValueError(
                f"input for 'variables' must be provided and non-empty for {self.name}"
                " algorithm plugin."
            )
        return self


class ColormapperArgumentsModel(PermissiveFrozenModel):
    """Validate Colormapper arguments."""

    pass


class ProductDefaultArgumentsModel(PermissiveFrozenModel):
    """Validate product default arguments."""

    pass


class ProductArgumentsModel(PermissiveFrozenModel):
    """Validate product arguments."""

    pass


class WorkflowArgumentsModel(PermissiveFrozenModel):
    """Validate Workflow arguments."""

    model_config = ConfigDict(extra="allow")
    pass


class GridlineAnnotatorArgumentsModel(PermissiveFrozenModel):
    """Validate Gridline Annotator arguments (YAML plugin)."""

    pass


class FeatureAnnotatorArgumentsModel(PermissiveFrozenModel):
    """Validate Feature Annotator arguments (YAML plugin)."""

    pass


class SectorArgumentsModel(PermissiveFrozenModel):
    """Validate Sector arguments (YAML plugin)."""

    pass


_PLUGIN_ARGUMENTS_MODELS: dict[str, type] = {
    "AlgorithmArgumentsModel": AlgorithmArgumentsModel,
    "ColormapperArgumentsModel": ColormapperArgumentsModel,
    "CoverageCheckerArgumentsModel": CoverageCheckerArgumentsModel,
    "FeatureAnnotatorArgumentsModel": FeatureAnnotatorArgumentsModel,
    "FilenameFormatterArgumentsModel": FilenameFormatterArgumentsModel,
    "GridlineAnnotatorArgumentsModel": GridlineAnnotatorArgumentsModel,
    "InterpolatorArgumentsModel": InterpolatorArgumentsModel,
    "OutputCheckerArgumentsModel": OutputCheckerArgumentsModel,
    "OutputFormatterArgumentsModel": OutputFormatterArgumentsModel,
    "ProductDefaultArgumentsModel": ProductDefaultArgumentsModel,
    "ProductArgumentsModel": ProductArgumentsModel,
    "ReaderArgumentsModel": ReaderArgumentsModel,
    "SectorArgumentsModel": SectorArgumentsModel,
    "WorkflowArgumentsModel": WorkflowArgumentsModel,
}


class GlobalVariablesModel(PermissiveFrozenModel):
    """Workflow-level global variables shared across all steps.

    Carries fields that apply uniformly to every step of an
    Order-Based Procflow workflow rather than belonging to a
    single step's arguments. (e.g. temporal windowing, product
    identification, product DB output configuration, and the
    presectoring toggle)
    """

    minimum_coverage: float | str = Field(default=PLUGIN_PROVIDED)
    presector: bool = Field(
        False,
        description="Specify whether to presector the data prior to applying "
        "the algorithm",
    )
    product_db: bool = Field(False)
    product_db_writer: str | None = Field(None)
    product_db_writer_kwargs: Dict[str, Any] | None = Field(None)
    product_name: str | None = Field(None)
    reader_defined_area_def: bool = Field(False)
    sector_list: List[str] | None = Field(None)
    window_start_time: dt.datetime | None = Field(
        None,
        description="If specified, sector temporally between window_start_time "
        "and window_end_time.",
    )
    window_end_time: dt.datetime | None = Field(
        None,
        description="If specified, sector temporally between window_start_time "
        "and window_end_time.",
    )

    @model_validator(mode="after")
    def _validate_product_db_requires_writer(
        cls, model: GlobalVariablesModel
    ) -> GlobalVariablesModel:
        """Validate that product_db is fully defined.

        If product_db is defined, then a corresponding product must be specified
        as a string in product_db_writer. Also check the opposite case, where
        product_db_writer is defined, but product_db is false.
        """
        if model.product_db and model.product_db_writer is None:
            raise ValueError(
                "product_db is set while product_db_writer is not defined. "
                "Please specify a valid product_db_writer."
            )
        if model.product_db_writer is not None and not model.product_db:
            raise ValueError(
                f"product_db_writer is defined as: `{model.product_db_writer}` "
                "but product_db is False or unspecified.\nPlease explicitly "
                "invoke 'product_db = True' or drop product_db_writer."
            )

        return model

    @model_validator(mode="after")
    def _validate_window_start_requires_end(
        cls, model: GlobalVariablesModel
    ) -> GlobalVariablesModel:
        """Validate the specified time range.

        If window_start_time is defined, then window_end_time must also be
        defined. The reverse situation is also checked.
        """
        if model.window_start_time is not None and model.window_end_time is None:
            raise ValueError(
                f"window_start_time is defined as `{model.window_start_time}` "
                "but there is no defined window_end_time. Please specify a "
                "window_end_time."
            )
        if model.window_end_time is not None and model.window_start_time is None:
            raise ValueError(
                f"window_end_time is defined as `{model.window_end_time}` "
                "but there is no defined window_start_time. Please specify a "
                "window_start_time."
            )

        return model


class WorkflowStepDefinitionModel(FrozenModel):
    """Validate step definition : kind, name, and arguments."""

    model_config = ConfigDict()

    kind: Lexeme = Field(..., description="plugin kind")
    name: str | tuple[str] | None = Field(
        None,
        description=(
            "Plugin name. Required for plugin-backed steps, but not for "
            "scaffold steps such as ``split`` or ``join`` or steps with "
            "``kind: workflow`` that supply an inline ``spec``."
        ),
    )
    spec: WorkflowSpecModel | None = Field(
        None, description="The workflow specification"
    )
    arguments: Dict[str, Any] | None = Field(
        default_factory=dict, description="step args"
    )
    depends_on: List[StepReference] | None = Field(
        None,
        description=(
            "Step references this step depends on. Each reference is either a "
            "top-level step id (e.g. 'reader') or a dot-separated path into a "
            "'workflow'/'split' container step (e.g. 'subwf.algo' or "
            "'split.scope.algo'), or the magic token '_input' marking this step "
            "as the workflow's data-injection entry point (parent data for a "
            "sub-workflow/branch, or an empty DataTree at top level). '_input' "
            "may be combined with real references and may appear on any number "
            "of steps (fan-out). If None, defaults to [previous_step_id] for "
            "non-first steps, [] for the first step; when no step declares "
            "'_input' the first step receives the injected data. The runner "
            "validates all references exist (recursing into sub-workflows) and "
            "that no cycles exist."
        ),
    )
    keep: bool = Field(
        False,
        description=(
            "If True, this step's output data dataset survives garbage "
            "collection regardless of the workflow-level retention policy. "
            "Metadata (attrs, tokens) always survive."
        ),
    )
    scope: str | None = Field(
        None,
        description=(
            "For steps following a ``split``: which branch to operate on. "
            "When set, this step's output node nests at "
            "``/<split_id>/<scope>/<step_id>``. "
            "Explicit step-level scope routing is not yet implemented."
        ),
    )
    when: str | None = Field(
        None,
        description=(
            "Conditional expression. If set and evaluates to false, this "
            "step is skipped. Expressions are pandas-style filter expressions. "
            "Runtime evaluation is not yet implemented."
        ),
    )
    full_test_policy: Literal["on_token_mismatch", "always", "never", None] = Field(
        None,
        description=(
            "Tells GeoIPS in what circumstances an output checker should run based on "
            "the result of the token comparison. Defaults to only running the specified"
            " (or detected) output checker on failed token comparison."
            "Should only EVER exist for an output checker step."
        ),
    )

    @field_validator("kind", mode="before")
    @classmethod
    def _validate_plugin_kind(cls, value: str) -> str:
        """
        Validate that 'kind' is a known plugin kind.

        Parameters
        ----------
        value : str
            Value of the 'kind' attribute to validate.

        Returns
        -------
        str
            Validated value of 'kind' if it is valid.

        Raises
        ------
        ValueError
            If the user-provided value for 'kind' is not in the valid_kind list.
        """
        # We did not switch to kind: Annotated[str, Field(pattern=kind_pattern)] due to
        # lack of user-friendly error reporting options in case of validation failure.

        if not value:
            raise ValueError("Invalid input: 'kind' cannot be empty.")

        valid_kinds = get_plugin_kinds()

        # Allow split/join as scaffolding (runtime raises NotImplementedError)
        valid_kinds = valid_kinds | SCAFFOLD_KINDS

        # raise error if the plugin kind is not valid
        if value not in valid_kinds:
            raise ValueError(
                f"[!] Invalid plugin kind: '{value}'. Must be one of {valid_kinds}\n\n"
            )

        return value

    @field_validator("scope", mode="before")
    @classmethod
    def _reject_scope(cls, value: str | None) -> None:
        """Reject non-None ``scope`` — explicit step-level scoping not implemented."""
        if value is not None:
            raise ValueError(
                "scope is not yet implemented — remove this field from the YAML"
            )
        return value

    @field_validator("when", mode="before")
    @classmethod
    def _reject_when(cls, value: str | None) -> None:
        """Reject non-None ``when`` — conditional execution is not yet implemented."""
        if value is not None:
            raise ValueError(
                "when is not yet implemented — remove this field from the YAML"
            )
        return value

    @model_validator(mode="before")
    def _ensure_xor_name_spec(cls, values):
        """Ensure that fields 'spec' and 'name' are mutually exclusive.

        Additionally, ensure that only workflow and split steps can define ``spec``.
        Plugin-backed steps must reference a name and provide arguments as usual.
        Join steps are scaffold steps and do not resolve a plugin by name.

        Parameters
        ----------
        values: dict
            Input values to the model.

        Returns
        -------
        values: dict
            Input values to the model.

        Raises
        ------
        ValueError
            If the plugin name is not valid for the specified plugin kind.
        """
        if not isinstance(values, dict):
            return values

        if values.get("kind") == "workflow":
            if (values.get("name") is None) == (values.get("spec") is None):
                raise ValueError("Exactly one of name or spec must be provided.")
            values["arguments"] = None
        elif values.get("kind") == "split":
            if values.get("name") is not None:
                raise ValueError("Split steps cannot define a plugin name.")
            if values.get("spec") is None:
                raise ValueError("Split steps must define an inline spec.")
        elif values.get("kind") == "join":
            if values.get("name") is not None:
                raise ValueError("Join steps cannot define a plugin name.")
            if values.get("spec") is not None:
                raise ValueError("Join steps cannot define an inline spec.")
        else:
            if values.get("spec"):
                raise ValueError(
                    "You cannot implement a spec field for any step other than "
                    "one which is a workflow or split."
                )
            if values.get("name") is None:
                raise ValueError(
                    "You must specify a name field for every plugin step that is not a "
                    "workflow, split, or join step."
                )

        return values

    @model_validator(mode="after")
    def _validate_plugin_name(
        cls,
        model: WorkflowStepDefinitionModel,
        info: ValidationInfo,
    ) -> WorkflowStepDefinitionModel:
        """
        Validate that a plugin with this name exists for the specified plugin kind.

        Parameters
        ----------
        model: WorkflowStepDefinitionModel
            The WorkflowStepDefinitionModel instance to validate.
        info: ValidationInfo
            ValidationInfo object, providing access to context flags.

        Returns
        -------
        WorkflowStepDefinitionModel
            The validated instance of WorkflowStepDefinitionModel

        Raises
        ------
        ValueError
            If the plugin name is not valid for the specified plugin kind.
        """
        plugin_name = model.name
        plugin_kind = model.kind

        if plugin_kind == "workflow" and model.spec is not None:
            # This occurs when we've converted a product or product default step to
            # an embedded workflow with a spec/steps section. No name is required.
            return model

        if plugin_kind in SCAFFOLD_KINDS:
            return model

        context = info.context or {}
        if context.get("skip_plugin_name_validation"):
            return model

        valid_plugin_names = get_plugin_names(plugin_kind)
        if plugin_name not in valid_plugin_names:
            raise ValueError(
                f"Invalid plugin name '{plugin_name}'."
                f"Must be one of {sorted(valid_plugin_names)}"
            )

        return model

    @model_validator(mode="after")
    def _validate_plugin_arguments(
        cls, model: WorkflowStepDefinitionModel
    ) -> WorkflowStepDefinitionModel:
        """
        Validate and organize details for each step.

        This validator is called after the model is initialized. It ensures that the
        `kind`, `name`, and `arguments` attributes are properly validated and
        structured for each workflow step.

        Parameters
        ----------
        model: WorkflowStepDefinitionModel
            The WorkflowStepDefinitionModel instance to validate.

        Returns
        -------
        WorkflowStepDefinitionModel
            The validated instance of WorkflowStepDefinitionModel
        """
        if model.arguments is None:
            # model.arguments is set to None when a workflow has been specified in place
            # I.e. an expanded product or a workflow with a spec section (no name)
            return model
        # Delegate arguments validation to each plugin kind argument class
        plugin_kind = model.kind

        if plugin_kind in (SCAFFOLD_KINDS | {"workflow"}):
            return model

        plugin_kind_pascal_case = "".join(
            [word.capitalize() for word in plugin_kind.split("_")]
        )
        plugin_arguments_model_name = f"{plugin_kind_pascal_case}ArgumentsModel"

        try:
            plugin_arguments_model = _PLUGIN_ARGUMENTS_MODELS[
                plugin_arguments_model_name
            ]
        except KeyError as e:
            valid_models = ", ".join(_PLUGIN_ARGUMENTS_MODELS)
            raise ValueError(
                f'The argument class/model "{plugin_arguments_model_name}" for '
                f'the plugin kind "{plugin_kind}" is not defined. Valid available '
                f"models are {valid_models}."
            ) from e

        plugin_arguments_model(**model.arguments)

        return model

    @model_validator(mode="after")
    def _validate_interpolator_step_depends_on_two(
        cls, model: WorkflowStepDefinitionModel
    ) -> WorkflowStepDefinitionModel:
        """
        Validate that if the step is an an interpolator, that it depends on two steps.

        This validator is called after the model is initialized. It ensures that the
        entire workflow is valid before perforing this validation. This is a corner
        case as it is one of few plugins that require exactly two steps to process
        correctly.

        Parameters
        ----------
        model: WorkflowStepDefinitionModel
            The WorkflowStepDefinitionModel instance to validate.

        Returns
        -------
        WorkflowStepDefinitionModel
            The validated instance of WorkflowStepDefinitionModel
        """
        if model.kind != "interpolator":
            return model

        dependencies = model.depends_on

        if not dependencies:
            return model

        if isinstance(dependencies, list) and len(dependencies) < 1:
            raise ValueError(
                "Error: 'depends_on' field must be specified for any interpolator step "
                "and it must depend on at least one step."
            )

        return model


class WorkflowSpecModel(FrozenModel):
    """The specification for a workflow."""

    # list of steps
    globals: GlobalVariablesModel | None = Field(
        None,
        description="Arguments shared across workflow steps",
    )
    steps: Dict[PythonIdentifier, WorkflowStepDefinitionModel] = Field(
        ..., description="Steps to produce the workflow."
    )

    retention: Literal["keep_all", "keep_referenced"] | None = Field(
        DEFAULT_RETENTION,
        description=(
            "Workflow-level data retention policy. "
            "- keep_all: never GC any step data. "
            "- keep_referenced: GC a step's data when no remaining "
            "  downstream step references it."
        ),
    )
    retention_by_kind: Dict[str, Literal["keep_all", "keep_referenced"]] | None = Field(
        None,
        description=(
            "Per-kind retention overrides. Keys are plugin kind names "
            "(e.g. 'reader', 'algorithm'). If None, no per-kind override. "
            "This is a v2 feature; field exists but is not wired in v1."
        ),
    )
    defaults: Dict[str, Dict[str, Any]] | None = Field(
        None,
        description=(
            "Per-kind argument defaults applied to every step of that kind. "
            "Keys are plugin kind names. Step-level arguments override these."
        ),
    )

    @model_validator(mode="after")
    def _reject_retention_by_kind(self):
        if self.retention_by_kind is not None:
            raise ValueError(
                "retention_by_kind is not yet implemented. "
                "Remove it from the YAML or set it to null."
            )
        return self

    @model_validator(mode="after")
    def _reject_defaults(self):
        """Reject ``defaults`` until the runtime wires it in.

        The field is accepted by the schema but never consumed by
        ``Workflow.call``; rejecting at validation prevents a spec from
        silently ignoring per-kind defaults.
        """
        if self.defaults is not None:
            raise ValueError(
                "defaults (per-kind argument defaults) is not yet implemented. "
                "Remove it from the YAML or set it to null."
            )
        return self

    @classmethod
    def extend_dict(cls, base: dict, new: dict) -> dict:
        """Extend a dictionary with the contents of another dictionary.

        Do this extension while avoiding key collisions by automatically renaming
        conflicting keys.

        Keys from ``new`` are added to ``base``. If a key from ``new`` already
        exists in ``base``, a numeric suffix is appended to the key name
        (e.g., ``key1``, ``key2``, etc.) until a unique key is found. The original
        dictionaries are not modified.

        Parameters
        ----------
        base: dict
            - The original dictionary whose contents will be preserved. Keys from
              ``new`` will be added to a copy of this dictionary.
        new: dict
            - The dictionary whose key-value pairs will be added to ``base``. If a
              key already exists in ``base`` (or was added earlier during the merge),
              it will be renamed with an incrementing numeric suffix to ensure
              uniqueness.

        Returns
        -------
        dict
            - A new dictionary containing all key-value pairs from ``base`` and
              ``new``. Any conflicting keys from ``new`` will be renamed with a
              numeric suffix (``key1``, ``key2``, etc.) so that no keys are overwritten.
        """
        result = deepcopy(base)

        for key, value in new.items():
            if key not in result:
                result[key] = value
                continue

            i = 1
            while f"{key}{i}" in result:
                i += 1

            result[f"{key}{i}"] = value

        return result

    @classmethod
    def product_to_steps(
        cls, plugin: dict, _inputs: list[str] | None = None
    ) -> tuple[dict[dict], dict]:
        """Define a product or product default plugin as a series of workflow steps.

        Parameters
        ----------
        plugin: dict
            A dictionary representation of a product or product default plugin.
        _inputs: list[str], optional
            One or more step ids that are providing input data to this step. Optional.
            If None, assume no input data is available or needed.

        Returns
        -------
        steps: dict[dict]
            - An ordered dictionary representing the expanded version of the input
              plugin.
        global_vars: dict
            - A dictionary of global variables found in this plugin.
        """
        steps = {}
        family = plugin.get("family")
        spec = plugin.get("spec", {})
        global_vars = {"variables": spec["variables"]} if spec.get("variables") else {}

        if family in ORDERED_PRODUCT_FAMILIES:
            step_order = family.split("_")
            last_data_step = []
            for idx, plugin_name in enumerate(step_order):
                steps[plugin_name] = spec[plugin_name].get("plugin")
                steps[plugin_name]["kind"] = plugin_name

                if plugin_name == "colormapper":
                    steps[plugin_name]["depends_on"] = []
                elif idx == 0 and _inputs:
                    steps[plugin_name]["depends_on"] = ["_input"]
                    last_data_step = [plugin_name]
                elif idx == 0 and not _inputs:
                    steps[plugin_name]["depends_on"] = []
                    last_data_step = [plugin_name]
                else:
                    steps[plugin_name]["depends_on"] = last_data_step
                    last_data_step = [plugin_name]

            if "coverage_checker" in spec:
                steps["coverage_checker"] = spec["coverage_checker"].get("plugin")
                steps["coverage_checker"]["kind"] = "coverage_checker"
                steps["coverage_checker"]["depends_on"] = last_data_step
        else:
            for key, value in spec.items():
                if key in ["mtif_type", "variables"]:
                    continue
                elif key == "windbarb_plotter":
                    kind = "output_formatter"
                else:
                    kind = key

                steps[key] = value.get("plugin")
                steps[key]["kind"] = kind

        if "coverage_checker" not in list(steps.keys()):
            # Add default coverage checker step if one doesn't already exist
            steps["coverage_checker"] = {
                "kind": "coverage_checker",
                "name": "masked_arrays",
                "depends_on": last_data_step,
                "arguments": {"minimum_coverage": 10},
            }

        return steps, global_vars

    @classmethod
    def expand_step(
        cls, step: dict, info: ValidationInfo, _inputs: list[str] | None = None
    ) -> dict[dict]:
        """Expand the definition of this step if it is a select plugin type.

        Plugin types this function will expand include
        ['products', 'product_defaults', 'workflows'].

        This function will fully expand this step if it is one of the mentioned types
        before any validation occurs.

        Parameters
        ----------
        step: dict
            A dictionary representation of a workflow step.
        info: ValidationInfo
            An object representing the context in which this model was instantiated.
        _inputs: list[str], optional
            One or more step ids that are providing input data to this step. Optional.
            If None, assume no input data is available or needed.

        Returns
        -------
        steps: dict[dict]
            - An ordered dictionary representing the expanded version of the input step.
        """
        context = info.context or {}
        expand = context.get("expand", False)

        kind = step.get("kind")
        interface = getattr(interfaces, Lexeme(kind).plural)

        if kind == "product":
            plugin = interface.get_plugin(*step.get("name"))
        elif kind == "product_default":
            plugin = interface.get_plugin(step.get("name"))
        else:
            # workflow plugins
            plugin = interface.get_plugin(step.get("name"), _expand=expand)

        if kind in ["product", "product_default"]:
            steps, global_vars = cls.product_to_steps(plugin, _inputs)  # NOQA
        else:
            steps = cls.expand_steps(plugin.get("spec"), info)["steps"]

        return steps

    @model_validator(mode="before")
    @classmethod
    def expand_steps(cls, data: dict, info: ValidationInfo):
        """Expand each step of a workflow if it is a select plugin type.

        Plugin types this function will expand include
        ['products', 'product_defaults', 'workflows'].

        This function will fully expand each step of the mentioned types before any
        validation occurs. This way workflows can support nested workflows, of which all
        of the mentioned types produce.
        """
        if data is None:
            return data

        context = info.context or {}
        expand = context.get("expand", False)

        steps = data.pop("steps", {})
        expanded_steps = {}

        _inputs = None

        for name, step in steps.items():
            if not isinstance(step, dict):
                expanded_steps[name] = step
                _inputs = [name]
                continue
            # Default
            if step.get("kind") in ["product", "product_default"]:
                if step.get("depends_on"):
                    _inputs = step["depends_on"]
                spec = {"steps": cls.expand_step(step, info, _inputs)}
                new_step = {
                    "kind": "workflow",
                    "spec": spec,
                }
                if step.get("depends_on"):
                    new_step["depends_on"] = step["depends_on"]
                # Generate a step ID based off the current step's plugin name.
                # For products, join the name tuple with "_" and replace any
                # remaining non-identifier characters so the result is always
                # a valid PythonIdentifier (required by depends_on validation).
                step_id = (
                    _product_step_id(step.get("name"))
                    if step.get("kind") == "product"
                    else step.get("name")
                )
                expanded_steps = cls.extend_dict(expanded_steps, {step_id: new_step})
            # Done for CLI calls to fully expand a workflow plugin
            elif (
                step.get("kind") == "workflow"
                and expand
                and (step.get("spec") is None or step.get("name"))
            ):
                expanded_steps = cls.extend_dict(
                    expanded_steps, cls.expand_step(step, info)
                )
            else:
                # Not a workflow or product-based plugin, just keep the step as it is
                expanded_steps[name] = step

            _inputs = [name]

        data["steps"] = expanded_steps

        mapping = {}
        for name, step in steps.items():
            if not isinstance(step, dict):
                continue
            if step.get("kind") in ("product", "product_default"):
                step_id = (
                    _product_step_id(step.get("name"))
                    if step.get("kind") == "product"
                    else step.get("name")
                )
                mapping[name] = [step_id]
            elif (
                step.get("kind") == "workflow"
                and expand
                and (step.get("spec") is None or step.get("name"))
            ):
                expanded = cls.expand_step(step, info)
                mapping[name] = list(expanded.keys())

        return data

    @model_validator(mode="before")
    @classmethod
    def _inject_defaults(cls, data: dict, info: ValidationInfo) -> dict:
        """Inject implicit defaults for ``depends_on``.

        Runs after ``expand_steps`` so the step dict is fully resolved.
        All defaults are baked into the raw dict *before* freezing, so no
        ``object.__setattr__`` is needed.
        """
        if data is None:
            return data
        steps = data.get("steps", {})
        step_ids = list(steps.keys())

        if not step_ids:
            return data

        if INPUT_REF in steps:
            raise ValueError(
                f"step id '{INPUT_REF}' is reserved: it is the magic "
                f"data-injection dependency token and cannot name a step"
            )

        for i, sid in enumerate(step_ids):
            step = steps[sid]
            if not isinstance(step, dict):
                continue
            if step.get("depends_on") is None:
                step["depends_on"] = [] if i == 0 else [step_ids[i - 1]]

        return data

    @staticmethod
    def _validate_reference_in_spec(spec, segments, dep, cur):
        """Recursively validate a dotted ``depends_on`` reference.

        Walks *segments* through *spec*'s steps, descending into ``workflow``
        and ``split`` container steps. ``split`` references must include a scope
        segment (``split.<scope>.<step>``) because a split nests its body once
        per branch (``/<split>/<scope>/<step>``); a bare ``split.<step>`` is
        ambiguous and rejected.

        Parameters
        ----------
        spec : WorkflowSpecModel
            The (sub-)workflow spec to resolve *segments* against.
        segments : list[str]
            Remaining dot-split reference segments.
        dep : str
            The full original reference (for error messages).
        cur : str
            The referencing step id (for error messages).
        """
        seg = segments[0]
        if seg not in spec.steps:
            raise PluginResolutionError(
                f"step '{cur}' depends_on '{dep}': '{seg}' is not a step in the "
                f"referenced workflow; valid steps: {sorted(spec.steps)}"
            )
        remaining = segments[1:]
        if not remaining:
            return

        step = spec.steps[seg]
        if step.kind not in ("workflow", "split"):
            raise PluginResolutionError(
                f"step '{cur}' depends_on '{dep}': '{seg}' is a '{step.kind}' "
                f"step and has no nested steps; only 'workflow' and 'split' "
                f"steps can be referenced with a dotted path"
            )
        if step.spec is None:
            raise PluginResolutionError(
                f"step '{cur}' depends_on '{dep}': container step '{seg}' has "
                f"no inline spec to resolve nested steps"
            )

        if step.kind == "split":
            if len(remaining) < 2:
                raise PluginResolutionError(
                    f"step '{cur}' depends_on '{dep}': references into a 'split' "
                    f"step must include a scope, e.g. '{seg}.<scope>.<step>'"
                )
            scope, remaining = remaining[0], remaining[1:]
            explicit_scopes = (step.arguments or {}).get("scopes")
            if explicit_scopes is not None and scope not in explicit_scopes:
                raise PluginResolutionError(
                    f"step '{cur}' depends_on '{dep}': scope '{scope}' is not a "
                    f"declared scope of split '{seg}'; valid scopes: "
                    f"{sorted(explicit_scopes)}"
                )

        WorkflowSpecModel._validate_reference_in_spec(step.spec, remaining, dep, cur)

    @model_validator(mode="after")
    def _validate_dependencies(self):
        """Validate ``depends_on`` refs and detect cycles.

        This is a read-only validator — all defaults have already been
        injected by ``_inject_defaults`` at mode="before".

        ``depends_on`` references may be dotted paths into ``workflow``/``split``
        container steps (e.g. ``subwf.algo``); these are validated by recursing
        into the container's inline spec. Cycle detection operates on the
        top-level *head* of each reference (the segment before the first dot).

        Raises
        ------
        PluginResolutionError
            If a ``depends_on`` reference (or nested segment) does not resolve.
        DependencyCycleError
            If the ``depends_on`` graph contains a directed cycle.
        """
        step_ids = list(self.steps.keys())

        if not step_ids:
            return self

        # --- deep-validate every depends_on reference (incl. dotted paths) ---
        # The magic ``_input`` token is a virtual source, not a real step, so it
        # is exempt from reference resolution.
        for cur, step in self.steps.items():
            for dep in step.depends_on or []:
                if dep == INPUT_REF:
                    continue
                self._validate_reference_in_spec(self, dep.split("."), dep, cur)

        # --- detect cycles on the top-level heads of each reference ---
        # Iterative three-color DFS (no recursion — safe for large workflows).
        # ``_input`` is a virtual source and never a graph node, so it is
        # dropped from the head set below.
        def _head(dep):
            return dep.split(".", 1)[0]

        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {sid: WHITE for sid in self.steps}

        for sid in self.steps:
            if color[sid] != WHITE:
                continue
            color[sid] = GRAY
            stack: list[tuple[str, int]] = [(sid, 0)]
            while stack:
                cur, idx = stack[-1]
                deps = [
                    _head(d)
                    for d in (self.steps[cur].depends_on or [])
                    if d != INPUT_REF
                ]
                if idx < len(deps):
                    stack[-1] = (cur, idx + 1)
                    dep = deps[idx]
                    if color.get(dep) == GRAY:
                        raise DependencyCycleError(
                            f"dependency cycle detected involving "
                            f"'{cur}' -> '{dep}'"
                        )
                    if color.get(dep) == WHITE:
                        color[dep] = GRAY
                        stack.append((dep, 0))
                else:
                    color[cur] = BLACK
                    stack.pop()

        return self


class OutputCheckerOverrideModel(PermissiveFrozenModel):
    """Model for output checker step definitions / overrides in a workflow test / steps section.  # NOQA

    Takes the form of:

    output_checker:
        name: my_oc
        full_test_policy: "on_token_mismatch" | "always" | "never"
        arguments:
        ...
    """

    name: Optional[str] = Field(
        None,
        description=(
            "The name of the output checker plugin to use. If None, use a default "
            "output checker plugin associated with the produced file type(s)."
        ),
        alias="output_checker_name",
    )
    compare_path: Union[FilePath, str, None] = Field(
        None,
        description="The path to the comparison file.",
    )
    threshold: Optional[float] = Field(
        None,
        description=(
            "Threshold for the image comparison. Argument to pixelmatch. Between "
            "0 and 1, with 0 the most strict comparison, and 1 the most lenient."
        ),
        alias="output_checker_threshold",
    )
    full_test_policy: Literal["on_token_mismatch", "always", "never"] = Field(
        "on_token_mismatch",
        description=(
            "Tells GeoIPS in what circumstances an output checker should run based on "
            "the result of the token comparison. Defaults to only running the specified"
            " (or detected) output checker on failed token comparison."
        ),
    )


class NestedSpecOverride(PermissiveFrozenModel):
    """Spec definition allowing for recursive overrides."""

    steps: Dict[str, StepOverrideType] = Field(default_factory=dict)


class StepOverrideType(PermissiveFrozenModel):
    """
    A workflow step override.

    Either:
    - arbitrary arguments
    OR
    - a nested spec containing additional steps
    """

    spec: Optional[NestedSpecOverride] = None


# Required for recursive references
NestedSpecOverride.model_rebuild()
StepOverrideType.model_rebuild()


class WorkflowTestModel(FrozenModel):
    """Model for the test section of GeoIPS workflow plugins."""

    # Not pathlib.Path objects as readers only expect a list of strings
    filenames: List[str] = Field(
        ...,
        description="A list of one or more filepaths to the data used for this test.",
        validation_alias=AliasChoices("fnames", "filenames"),
    )
    #
    # globals:
    #   argument: value
    #
    globals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Override dictionary for global arguments.",
    )

    #
    # kinds:
    #     readers:
    #         argument: value
    #
    # Keys must match interfaces.__all__
    #
    kinds: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Override dictionary for plugins matching a certain 'kind'.",
    )

    #
    # steps:
    #     step_id:
    #         argument: value
    #
    # or recursive nested specs
    #
    steps: Dict[str, StepOverrideType] = Field(
        default_factory=dict,
        description="Override dictionary for individual steps.",
    )

    #
    # outputs:
    #     step_id:
    #         # name: optional, default=None, derived from 'compare_path' if not provided  # NOQA
    #         # full_test_policy: optional, default="on_token_mismatch"
    #         output_checker_arguments:
    #             compare_path: <path_to_compare_file>
    #             optional_arg1: <x>
    #             optional_arg2: <z>

    outputs: Dict[str, OutputCheckerOverrideModel] = Field(
        default_factory=dict,
        description=(
            "Override dictionary for output checker steps or every instance of"
            " an output checker."
        ),
    )

    @model_validator(mode="after")
    def validate_kind_keys(self) -> WorkflowTestModel:
        """Ensure kinds keys are valid GeoIPS interfaces."""
        # Make sure any element of kinds are a valid interface
        invalid = set(self.kinds) - set(interfaces.__all__)

        if invalid:
            raise ValueError(
                f"Invalid kinds keys: {sorted(invalid)}. "
                f"Valid interfaces are: {sorted(interfaces.__all__)}"
            )

        return self

    @field_validator("filenames", mode="before")
    @classmethod
    def generate_filepaths(cls, v):
        """Convert a single string or list of strings to pathlib.Path objects."""
        if (
            not isinstance(v, str)
            and not isinstance(v, list)
            and not isinstance(v, tuple)
        ):
            raise ValueError(
                f"Error, got {v} but expected a single string or list of strings."
            )

        filepaths = v if isinstance(v, list) else [v]
        final_paths = []

        # cspell:ignore ipath, jpath, jpaths
        for ipath in filepaths:
            jpaths = sorted(glob(ipath))
            for jpath in jpaths:
                # Don't do pathlib.Path as readers don't expect that.
                final_paths.append(jpath)

        return final_paths


class WorkflowPluginModel(PluginModel):
    """A plugin that produces a workflow."""

    model_config = ConfigDict(extra="allow")
    test: WorkflowTestModel = Field(
        None,
        description=(
            "An optional dictionary of parameters used to test this workflow.",
        ),
        examples=[
            {
                "fnames": f"{config.testdata_dir}/test_data_abi/data/goes16_20200918_1950/*",  # NOQA
                "command_line_args": {
                    "compare_path": f"{config.packages_dir}/geoips/tests/outputs/abi.static.<product>.imagery_clean",  # NOQA
                    "logging_level": "info",
                },
            },
        ],
    )
    spec: WorkflowSpecModel = Field(..., description="The workflow specification")

    @model_validator(mode="before")
    @classmethod
    def propagate_context(cls, data: dict, info: ValidationInfo):
        """Propagate context to the spec model if it exists.

        This should only occur for 'geoips expand <workflow>' calls.
        """
        context = info.context or {}

        spec_data = data.get("spec")
        if spec_data and len(list(context.keys())):
            # Re-validate spec WITH context
            data["spec"] = WorkflowSpecModel.model_validate(
                spec_data,
                context=context,
            )

        return data
