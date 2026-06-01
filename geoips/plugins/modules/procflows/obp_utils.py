# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Order-Based Procflow (OBP) utility functions."""

# Python Standard Libraries
from importlib import import_module

# GeoIPS imports
from geoips.utils.types.partial_lexeme import Lexeme
from geoips.constants import PLUGIN_PROVIDED

interface = None


def validate_arguments(apiVersion, interface, arguments):
    """Load the correct pydantic argument model and validate arguments.

    Where the 'correct' argument model is based on apiVersion and interface.

    Parameters
    ----------
    apiVersion : str
        The apiVersion of the workflow model that contained these arguments.
    interface : str
        The name of the interface we'll provide arguments to.
    arguments : dict[str, Any]
        A dictionary of arguments to validate against a certain model.

    Returns
    -------
    validated_arguments : dict[str, Any]
        A validated representation of the input arguments.
    """
    package, version = apiVersion.split("/")
    try:
        module = import_module(f"{package}.pydantic_models.{version}.{interface}")
    except ImportError as e:
        raise ImportError(f"Could not import models from '{version}': {e}") from e

    interface_base = str(Lexeme(interface).singular)
    model_name = f"{interface_base.title().replace('_', '')}ArgumentsModel"

    try:
        model_class = getattr(module, model_name)
    except AttributeError as e:
        raise ValueError(f"Model '{model_name}' not found in '{apiVersion}'") from e

    return model_class(**arguments).model_dump()


def remove_keys_with_default_value_plugin_provided(workflow_dict: dict) -> dict:
    """Sanitize the workflow by removing keys with value 'PLUGIN_PROVIDED'.

    'PLUGIN_PROVIDED' acts as a secondary default value in the OBP. It is used when the
    same argument across different plugins of the same type has different default
    values.

    This function recursively removes workflow arguments whose value is
     'PLUGIN_PROVIDED'. The plugin call signature would process these arguemnts as
     ommited and populates the default value accordingly.

    Parameters
    ----------
    workflow: dict
        The workflow plugin dictionary to process.

    Returns
    -------
    dict
        workflow dictionary with all keys containing the value 'plugin_provided'
         removed.
    """
    if isinstance(workflow_dict, dict):
        return {
            key: remove_keys_with_default_value_plugin_provided(val)
            for key, val in workflow_dict.items()
            if val != PLUGIN_PROVIDED
        }
    return workflow_dict
