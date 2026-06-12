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
from typing import Any, Dict, List, Literal, Optional, Union

# Third-Party Libraries
from pydantic import (
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    ValidationInfo,
)

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic_models.v1.bases import (
    PluginModel,
    FrozenModel,
    PermissiveFrozenModel,
    PythonIdentifier,
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

Steps with these kinds are accepted by schema validation but raise
``NotImplementedError`` at runtime.
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
            "Plugin name. Required for every step except those with "
            "``kind: workflow`` that supply an inline ``spec``."
        ),
    )
    spec: WorkflowSpecModel | None = Field(
        None, description="The workflow specification"
    )
    arguments: Dict[str, Any] | None = Field(
        default_factory=dict, description="step args"
    )
    depends_on: List[str] | None = Field(
        None,
        description=(
            "Step IDs this step depends on. If None, defaults to "
            "[previous_step_id] for non-first steps, [] for the first step. "
            "The runner validates all references exist and no cycles exist."
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
            "Split/join execution is not yet implemented."
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
        """Reject non-None ``scope`` — split/join is not yet implemented."""
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

        Additionally, ensure that only workflow plugins can define spec in a step. All
        other plugins must reference a name and provide arguments as is done usually.

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
        if values.get("kind") == "workflow":
            if (values.get("name") is None) == (values.get("spec") is None):
                raise ValueError("Exactly one of 'name' or 'spec' must be provided.")
            values["arguments"] = None
        else:
            if values.get("spec"):
                raise ValueError(
                    "You cannot implement a 'spec' field for any step other than one "
                    "which a workflow."
                )
            if values.get("name") is None:
                raise ValueError(
                    "You must specify a name field for every plugin step that is not a "
                    "workflow step."
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


class WorkflowSpecModel(FrozenModel):
    """The specification for a workflow."""

    # list of steps
    global_arguments: GlobalVariablesModel | None = Field(
        None, description="Arguments shared across workflow steps"
    )
    steps: Dict[
        str, Union[WorkflowStepDefinitionModel, OutputCheckerStepDefinition]
    ] = Field(..., description="Steps to produce the workflow.")

    outputs: List[str] | None = Field(
        None,
        description=(
            "Step IDs that constitute workflow outputs. These step nodes "
            "are exempt from garbage collection. If None, defaults to "
            "[last_step_id] using Python 3.7+ dict insertion ordering."
        ),
    )
    retention: Literal["keep_all", "keep_referenced", "keep_outputs_only"] | None = (
        Field(
            DEFAULT_RETENTION,
            description=(
                "Workflow-level data retention policy. "
                "- keep_all: never GC any step data. "
                "- keep_referenced: GC a step's data when no remaining "
                "  downstream step references it. "
                "- keep_outputs_only: GC everything except declared outputs."
            ),
        )
    )
    retention_by_kind: (
        Dict[str, Literal["keep_all", "keep_referenced", "keep_outputs_only"]] | None
    ) = Field(
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
    def product_to_steps(cls, plugin: dict) -> tuple[dict[dict], dict]:
        """Define a product or product default plugin as a series of workflow steps.

        Parameters
        ----------
        plugin: dict
            - A dictionary representation of a product or product default plugin.

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
            for plugin_name in family.split("_"):
                steps[plugin_name] = spec[plugin_name].get("plugin")
                steps[plugin_name]["kind"] = plugin_name
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

        return steps, global_vars

    @classmethod
    def expand_step(cls, step: dict, info: ValidationInfo) -> dict[dict]:
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
            steps, global_vars = cls.product_to_steps(plugin)  # NOQA
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

        for name, step in steps.items():
            # Default
            if step.get("kind") in ["product", "product_default"]:
                spec = {"steps": cls.expand_step(step, info)}
                new_step = {
                    "kind": "workflow",
                    "spec": spec,
                }
                # Generate a step ID based off the current step's plugin name
                # if it's a product, merge the name tuple into a single name
                step_id = (
                    ":".join(step.get("name"))
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

        data["steps"] = expanded_steps

        return data

    @model_validator(mode="before")
    @classmethod
    def _inject_defaults(cls, data: dict, info: ValidationInfo) -> dict:
        """Inject implicit defaults for ``outputs`` and ``depends_on``.

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

        if data.get("outputs") is None:
            data["outputs"] = [step_ids[-1]]

        for i, sid in enumerate(step_ids):
            step = steps[sid]
            if step.get("depends_on") is None:
                step["depends_on"] = [] if i == 0 else [step_ids[i - 1]]

        return data

    @model_validator(mode="after")
    def _validate_dependencies(self):
        """Validate ``outputs`` refs, ``depends_on`` refs, and detect cycles.

        This is a read-only validator — all defaults have already been
        injected by ``_inject_defaults`` at mode="before".

        Raises
        ------
        DanglingOutputError
            If an entry in ``outputs`` is not a defined step id.
        PluginResolutionError
            If a ``depends_on`` value references a non-existent step id.
        DependencyCycleError
            If the ``depends_on`` graph contains a directed cycle.
        """
        from geoips.errors import (
            DanglingOutputError,
            DependencyCycleError,
            PluginResolutionError,
        )

        step_ids = list(self.steps.keys())

        if not step_ids:
            return self

        # --- validate outputs reference valid steps ---
        unknown_outputs = set(self.outputs or []) - set(step_ids)
        if unknown_outputs:
            raise DanglingOutputError(
                f"outputs {sorted(unknown_outputs)} are not defined step ids; "
                f"valid ids: {sorted(step_ids)}"
            )

        # --- validate depends_on references & detect cycles ---
        # Iterative three-color DFS (no recursion — safe for large workflows).
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {sid: WHITE for sid in self.steps}

        for sid in self.steps:
            if color[sid] != WHITE:
                continue
            color[sid] = GRAY
            stack: list[tuple[str, int]] = [(sid, 0)]
            while stack:
                cur, idx = stack[-1]
                deps = self.steps[cur].depends_on or []
                if idx < len(deps):
                    stack[-1] = (cur, idx + 1)
                    dep = deps[idx]
                    if dep not in self.steps:
                        raise PluginResolutionError(
                            f"step '{cur}' depends_on '{dep}', "
                            f"which is not a defined step id"
                        )
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


class OutputCheckerStepDefinition(PermissiveFrozenModel):
    """Model for output checker step definitions / overrides in a workflow test / steps section.  # NOQA

    Takes the form of:

    output_checker:
        name: my_oc
        policy: "on_failure" | "always"
        arguments:
        ...
    """

    name: Optional[str] = Field(
        None,
        description=(
            "The name of the output checker plugin to use. If None, use a default "
            "output checker plugin associated with the produced file type(s)."
        ),
    )
    arguments: OutputCheckerArgumentsModel = Field(
        ...,
        description=(
            "A dictionary of arguments to be supplied to an output_checker plugin."
        ),
        alias="output_checker_arguments",
    )
    policy: Literal["on_failure", "always"] = Field(
        "on_failure",
        description=(
            "Whether or not to run the output checker based on the result of "
            "the token comparison. Defaults to only running the specified (or detected)"
            " output checker on failed token comparison."
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
    fnames: List[str] = Field(
        ...,
        description="A list of one or more filepaths to the data used for this test.",
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
    #         # policy: optional, default="on_failure"
    #         output_checker_arguments:
    #             compare_path: <path_to_compare_file>
    #             optional_arg1: <x>
    #             optional_arg2: <z>

    outputs: Dict[str, OutputCheckerStepDefinition] = Field(
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

    @field_validator("fnames", mode="before")
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
