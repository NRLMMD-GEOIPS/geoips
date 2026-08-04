# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for generic rgb recipes."""

import numpy
from pandas.io.formats.format import math

from geoips.interfaces.class_based.algorithms import BaseAlgorithmPlugin
from geoips.interfaces import algorithm_configs

import logging

import ast
import operator

LOG = logging.getLogger(__name__)


class ConfigRgbAlgorithmPlugin(BaseAlgorithmPlugin):
    """Congig rgb algorithm plugin class."""

    interface = "algorithms"
    family = "xarray_to_numpy"
    name = "config_rgb"

    # map each mathematical symbol to a corresponding numpy function
    _operations = {
            ast.Add : numpy.add,
            ast.Sub : numpy.subtract,
            ast.Mult : numpy.multiply,
            ast.Div : numpy.divide,
            ast.Pow : numpy.pow,
    }

    @classmethod
    def _safe_eval(cls, node, variables):
        '''Parses user-inputted expressions recursively.

        Parameters
        ----------
        node : ast.Constant | ast.Name | ast.BinOp | ast.Call
            A node representative of a section of the expression.
        variables : dict[str : np.MaskedArray] 
            A dictionary to map each variable inputted by 
            the user to its corresponding MaskedArray
        '''
        if isinstance(node, ast.Constant):
            # Numeric constants, e.g. 1
            return node.value
        elif isinstance(node, ast.Name):
            # Varibles from the `variables` dictionary
            return variables[node.id]
        elif isinstance(node, ast.BinOp):
            # Binary operations, e.g addition.
            op = cls._operations[node.op.__class__]
            left = cls._safe_eval(node.left, variables)
            right = cls._safe_eval(node.right, variables)
            return op(left, right)
        elif isinstance(node, ast.Call):
            # check if the call is valid
            assert isinstance(node.func, ast.Name)
            # if not a valid numpy function, it will throw an AttributeError
            func = getattr(numpy, node.func.id)
            args = [cls._safe_eval(arg, variables) for arg in node.args]
            return func(*args)

        # some unknown node type
        assert False, 'Unsafe operation'


    @classmethod
    def safe_eval(cls, expression, variables):
        '''Wrapper for recursive expression evaluator `_safe_eval`

        Parameters
        ----------
        expression : str
            A string representing the `expression` user input in the algorithm_configs
            yaml file.
        variables : dict[str : np.MaskedArray]
            A dictionary to map each variable inputted by 
            the user to its corresponding MaskedArray
        
        Returns
        -------
        data : numpy.ndarray
            The resulting dataset after parsing and performing the equation.
        '''
        node = ast.parse(expression, '<string>', 'eval').body
        return cls._safe_eval(node, variables)
    
    @classmethod
    def apply_equation(cls, xobj, equation):
        """Apply the provided equation to data contained in xobj.

        Parameters
        ----------
        xobj : xarray.Dataset
            The input dataset to perform an equation on.
        equation : dict[str, Any]
            The equation to perform on input data.

        Returns
        -------
        data : numpy.ndarray
            The resulting dataset after performing the equation.
        """
        equation_type = equation["type"]

        if equation_type == "expression":
            variables = {}
            for v in equation["variables"]:
                variables[v] = xobj[v].to_masked_array()
            return cls.safe_eval(equation["expression"], variables)

        if equation_type == "addition":
            data = (
                xobj[equation["variables"][0]].to_masked_array()
                + xobj[equation["variables"][1]].to_masked_array()
            )
        elif equation_type == "difference":
            data = (
                xobj[equation["variables"][0]].to_masked_array()
                - xobj[equation["variables"][1]].to_masked_array()
            )
        else:
            data = xobj[equation["variables"][0]].to_masked_array()

        return data

    def call(self, xobj, config_name):  # NOQA -- xobj is used in the literal eval calls
        """Apply a generic algorithm for rgb recipes.

        Parameters
        ----------
        xobj : xarray.Dataset
            The dataset containing variables needed for a given rgb recipe.
        config_name : str
            The name of the config plugin that contains the RGB recipe.

        Returns
        -------
        numpy.ndarray
            numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output
        """
        config = algorithm_configs.get_plugin(config_name)

        red = self.apply_equation(xobj, config["spec"]["red"]["equation"])
        grn = self.apply_equation(xobj, config["spec"]["green"]["equation"])
        blu = self.apply_equation(xobj, config["spec"]["blue"]["equation"])

        input_units_red = config["spec"]["red"]["input_units"]
        output_units_red = config["spec"]["red"]["output_units"]
        input_units_grn = config["spec"]["green"]["input_units"]
        output_units_grn = config["spec"]["green"]["output_units"]
        input_units_blu = config["spec"]["blue"]["input_units"]
        output_units_blu = config["spec"]["blue"]["output_units"]

        # Convert TB from Kevin to Celsius
        from geoips.data_manipulations.conversions import unit_conversion

        red = unit_conversion(
            red, input_units=input_units_red, output_units=output_units_red
        )
        grn = unit_conversion(
            grn, input_units=input_units_grn, output_units=output_units_grn
        )
        blu = unit_conversion(
            blu, input_units=input_units_blu, output_units=output_units_blu
        )

        from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

        data_range = config["spec"]["red"]["data_range"]
        gamma = config["spec"]["red"]["gamma"]
        red = apply_data_range(
            red,
            min_val=data_range[0],
            max_val=data_range[1],
            min_outbounds="crop",
            max_outbounds="crop",
            norm=True,
            inverse=False,
        )  # need inverse option?
        red = apply_gamma(red, gamma)

        data_range = config["spec"]["green"]["data_range"]
        gamma = config["spec"]["green"]["gamma"]
        grn = apply_data_range(
            grn,
            min_val=data_range[0],
            max_val=data_range[1],
            min_outbounds="crop",
            max_outbounds="crop",
            norm=True,
            inverse=False,
        )
        grn = apply_gamma(grn, gamma)

        data_range = config["spec"]["blue"]["data_range"]
        gamma = config["spec"]["blue"]["gamma"]
        blu = apply_data_range(
            blu,
            min_val=data_range[0],
            max_val=data_range[1],
            min_outbounds="crop",
            max_outbounds="crop",
            norm=True,
            inverse=False,
        )  # create image of deep clouds in blueish color
        # norm=True, inverse=False)    #create image of deep clouds in yellowish color
        blu = apply_gamma(blu, gamma)

        from geoips.image_utils.mpl_utils import (
            alpha_from_masked_arrays,
            rgba_from_arrays,
        )

        alp = alpha_from_masked_arrays([red, grn, blu])
        rgba = rgba_from_arrays(red, grn, blu, alp)

        return rgba


PLUGIN_CLASS = ConfigRgbAlgorithmPlugin
