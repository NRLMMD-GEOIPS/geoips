"""Simple validation of the difference between two xarray objects."""

import logging

import xarray

LOG = logging.getLogger(__name__)

interface = "validators"
name = "difference"
family = "standard"


def call(xarray_obj, truth_xarray_obj, vars_to_validate=[]):
    """Calculate and validate the difference between output and truth.

    Where output in this case is xarray_obj and truth is truth_xarray_obj. Difference
    will be calculated for every field that exists and is the same between the two
    datasets, or, if supplied, the variables contained in vars_to_validate.

    Parameters
    ----------
    xarray_obj: xarray.Dataset
        - The produced xarray.Dataset from some routine
    truth_xarray: xarray.Dataset
        - An xarray.Dataset from a known source of truth.
    vars_to_validate: list, default=[]
        - A list of variables to validate against. If empty, all variables that exist
          and are the same between xarray_obj and truth_xarray_obj will be validated
          instead.
    """
    output_vars = list(xarray_obj.variables.keys())
    truth_vars = list(truth_xarray_obj.variables.keys())
    common_vars = set(output_vars).intersection(truth_vars)
    compare_vars = vars_to_validate if len(vars_to_validate) else common_vars

    diff_vars = {}

    for varname in compare_vars:
        if len(vars_to_validate) and varname not in common_vars:
            raise LookupError(
                f"Error: Variable '{varname}' couldn't be found in the produced "
                "xarray, truth xarray, or both xarrays. Validation cannot proceed."
            )
        diff = (
            xarray_obj.variables[varname].data
            - truth_xarray_obj.variables[varname].data
        )
        diff_vars[varname] = diff

    final_xobj = xarray.Dataset(
        data_vars=diff_vars,
        coords=xarray_obj.coords,
        attrs=dict(xarray_obj.attrs).update(dict(truth_xarray_obj.attrs)),
    )

    return final_xobj
