# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""GeoIPS deprecation helpers."""

import functools
from typing import Annotated, Any, Callable, Literal, Self
import warnings

import deprecate as pydeprecate
from deprecate import TargetMode
from pydantic import AnyUrl, BaseModel, Field
from pydantic_extra_types.semantic_version import SemanticVersion
import yaml


class GeoipsDeprecationMessage(BaseModel):
    """Validation model for standard GeoIPS deprecation string."""

    name: str | None = Field(
        default=None,
        alias="Name",
        max_length=70,
        description=(
            "A nice, human-readable 'name' to give this deprecation, as displayed in "
            "docs and warning messages. (Useful when deprecating some functionality "
            "whose Python API name may not be helpful to the user or developer "
            "encountering the deprecation.)"
        ),
    )
    component: Annotated[
        str,
        Field(
            alias="Component",
            max_length=40,
            description="Component of GeoIPS in which this deprecation is located.",
        ),
    ]
    reference_issue: Annotated[
        AnyUrl | Literal["MISSING"],
        Field(
            alias="Reference Issue",
            description=(
                "Canonical reference issue on GitHub (or GitLab, etc.) for this "
                "deprecation, containing all anciliary information relevant for "
                "developers."
            ),
        ),
    ]
    deprecated_in: Annotated[
        SemanticVersion,
        Field(
            alias="Deprecated In",
            description=(
                "Version in which this deprecated functionality begins to issue a "
                "warning."
            ),
        ),
    ]
    remove_in: SemanticVersion | Literal["Conditional (see issue)"] | None = Field(
        default="Conditional (see issue)",
        alias="Removal In",
        description=(
            "Version in which this deprecated functionality is to be removed and raise "
            "an error instead."
        ),
    )
    replacement: str | None = Field(
        default=None,
        alias="Replacement",
        max_length=90,
        description=(
            "A short description of what should be used instead of this deprecated "
            "functionality. For more complex migrations, a replacement message like "
            "'Consult the migration guide at INSERT-URL-HERE' is recommended."
        ),
    )

    @classmethod
    def parse_message(cls, message: str) -> Self:
        """Parse YAML-formatted text string into the data model.

        Parameters
        ----------
        message: str
            The YAML-formatted message string

        Returns
        -------
        GeoipsDeprecationMessage
            The (validated) Pydantic data model with relevant fields available

        """
        return cls.model_validate(yaml.load(message, Loader=yaml.BaseLoader))


class GeoipsDeprecationWarning(DeprecationWarning):
    """GeoIPS-specific DeprecationWarning."""

    def __init__(self, message):
        """We expect multiline messages; reformat without newlines."""
        # TODO: Consider more complete reformat, since that is more or less already
        # happening in the PyDeprecate wrapper anyway?
        super().__init__(
            " - ".join(line.strip() for line in message.splitlines() if line.strip())
        )


class GeoipsPendingDeprecationWarning(PendingDeprecationWarning):
    """GeoIPS-specific PendingDeprecationWarning."""

    def __init__(self, message):
        """We expect multiline messages; reformat without newlines."""
        # TODO: Consider more complete reformat, since that is more or less already
        # happening in the PyDeprecate wrapper anyway?
        super().__init__(
            " - ".join(line.strip() for line in message.splitlines() if line.strip())
        )


# Define our callable streams for pydeprecate
deprecation_warning = functools.partial(
    warnings.warn, category=GeoipsDeprecationWarning
)
pending_deprecation_warning = functools.partial(
    warnings.warn, category=GeoipsPendingDeprecationWarning
)


def _parse_for_pydeprecate(
    message: str, include_docstring_args: bool = True, **kwargs
) -> dict[str, Any]:
    """Update PyDeprecate kwargs from a standard GeoIPS deprecation message."""
    # Grab message contents
    contents = GeoipsDeprecationMessage.parse_message(message)

    # Set deprecation lifecycle arguments
    for parsed_kwarg in ("deprecated_in", "remove_in"):
        if getattr(contents, parsed_kwarg, None):
            kwargs[parsed_kwarg] = str(getattr(contents, parsed_kwarg))

    # Set custom message
    name = getattr(contents, "name", None)
    name = "`%(source_name)s`" if name is None else name
    pydeprecate_message = (
        f"{name} (Component: {contents.component}) is deprecated as of "
        "v%(deprecated_in)s"
    )
    if "remove_in" in kwargs and not kwargs["remove_in"].startswith("Conditional"):
        pydeprecate_message += ", and will be removed in v%(remove_in)s. "
    else:
        pydeprecate_message += ". "
    if getattr(contents, "replacement", None):
        pydeprecate_message += (
            f"Replacement/Migration Instructions: {contents.replacement}. "
        )
    if contents.reference_issue != "MISSING":
        pydeprecate_message += f"See {contents.reference_issue} for more information."
    if "message_template" in kwargs:
        warnings.warn(
            (
                "GeoIPS deprecation utils overwrite the PyDeprecate "
                "`message_template`; all relevant information should be included in "
                "the standard warning message YAML-formatted string."
            ),
            UserWarning,
        )
    kwargs["message_template"] = pydeprecate_message.strip()

    # Set geoips defaults, if not overwritten
    if "stream" not in kwargs:
        kwargs["stream"] = deprecation_warning
    if include_docstring_args:
        if "update_docstring" not in kwargs:
            kwargs["update_docstring"] = True
        if "docstring_style" not in kwargs:
            kwargs["docstring_style"] = "rst"

    return kwargs


def deprecate_module(message: str, name: str | None = None, **kwargs) -> None:
    r"""Deprecate the specified module.

    This is a wrapper of PyDeprecate's ``deprecated_module``, parsing the standard
    GeoIPS deprecation message string and setting GeoIPS defaults.

    Parameters
    ----------
    message: str
        The YAML-formatted message string
    name: str, optional
        The module name, typically as given by ``__name__``
    \*\*kwargs
        Keyword arguments passed on to PyDeprecate.
    """
    kwargs = _parse_for_pydeprecate(message, include_docstring_args=False, **kwargs)
    return pydeprecate.deprecated_module(name, **kwargs)


def deprecate_callable(message: str | None = None, **kwargs) -> Callable:
    r"""Deprecate the decorated callable.

    This is a wrapper of PyDeprecate's ``deprecated``, parsing the standard GeoIPS
    deprecation message string and setting GeoIPS defaults. This should be placed
    *after* the PEP 702 `@deprecated` decorator, if used (be sure to set
    ``category=None`` in that decorator, to not issue duplicate warnings).

    Parameters
    ----------
    message: str, optional
        The YAML-formatted message string. This is usually left empty, and parsed
        instead from the ``__deprecated__`` attribute, as attached by the PEP 702
        ``@deprecated`` decorator.
    \*\*kwargs
        Keyword arguments passed on to PyDeprecate.

    Notes
    -----
    TODO: Consider removing the ``message`` argument and instead requiring the
    preferred pattern of following after the PEP 702 deprecation.
    """  # noqa: D202

    # Annotating as "Any", since PyDeprecate annotates with a private type
    def decorator(func: Callable) -> Any:
        nonlocal message, kwargs
        if not message and getattr(func, "__deprecated__", None):
            message = func.__deprecated__
        kwargs = _parse_for_pydeprecate(message, **kwargs)
        return pydeprecate.deprecated(**kwargs)(func)

    return decorator


def deprecate_argument(message: str, **kwargs) -> Callable:
    r"""Deprecate a particular argument name on the decorated callable.

    This is a wrapper of PyDeprecate's ``deprecated``, parsing the standard GeoIPS
    deprecation message string and setting GeoIPS defaults.

    Parameters
    ----------
    message: str
        The YAML-formatted message string.
    \*\*kwargs
        Keyword arguments passed on to PyDeprecate. ``args_mapping`` must be included.

    Notes
    -----
    ``args_mapping`` is set as ``{"old": "new"}`` for renames, ``{"old": None}`` to
    drop.
    TODO: Consider validating here that ``args_mapping`` is provided as a keyword
    argument, rather than letting it raise from PyDeprecate.
    """
    kwargs = _parse_for_pydeprecate(message, **kwargs)
    return pydeprecate.deprecated(target=TargetMode.ARGS_REMAP, **kwargs)


def deprecate_instance(obj: Any, message: str, **kwargs) -> None:
    r"""Deprecate the specified instance of an object.

    This is a wrapper of PyDeprecate's ``deprecated_instance``, parsing the standard
    GeoIPS deprecation message string and setting GeoIPS defaults.

    Parameters
    ----------
    obj
        The particular Python object whose usage is to be deprecated
    message: str
        The YAML-formatted message string
    \*\*kwargs
        Keyword arguments passed on to PyDeprecate.
    """
    kwargs = _parse_for_pydeprecate(message, include_docstring_args=False, **kwargs)
    return pydeprecate.deprecated_instance(obj, **kwargs)


def deprecate_class(message: str | None = None, **kwargs) -> Callable:
    r"""Deprecate the decorated class.

    This is a wrapper of PyDeprecate's ``deprecated_class``, parsing the standard
    GeoIPS deprecation message string and setting GeoIPS defaults. This should be
    placed *after* the PEP 702 ``@deprecated`` decorator, if used (be sure to set
    ``category=None`` in that decorator, to not issue duplicate warnings).

    Parameters
    ----------
    message: str, optional
        The YAML-formatted message string. This is usually left empty, and parsed
        instead from the ``__deprecated__`` attribute, as attached by the PEP 702
        ``@deprecated`` decorator.
    \*\*kwargs
        Keyword arguments passed on to PyDeprecate.

    Notes
    -----
    TODO: Consider removing the ``message`` argument and instead requiring the preferred
    pattern of following after the PEP 702 deprecation.
    """  # noqa: D202

    # Annotating as "Any", since PyDeprecate annotates with a private type
    def decorator(cls: Any) -> Any:
        nonlocal message, kwargs
        if not message and getattr(cls, "__deprecated__", None):
            message = cls.__deprecated__
        kwargs = _parse_for_pydeprecate(message, **kwargs)
        return pydeprecate.deprecated_class(**kwargs)(cls)

    return decorator
