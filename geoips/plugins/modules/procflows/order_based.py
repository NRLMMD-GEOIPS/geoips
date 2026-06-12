# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Processing workflow for order-based data source processing.

The ``OrderBased`` class replaces the legacy module-level ``call()``
function.  External callers should resolve through the procflows registry:
``interfaces.procflows.get_plugin("order_based")(workflow_spec, fnames=fnames)``.
"""

from __future__ import annotations

import logging
from glob import glob
from typing import Any

from geoips.interfaces.class_based.procflows import BaseProcflowPlugin
from geoips.interfaces.class_based.workflow import Workflow
from geoips.pydantic_models.v1.workflows import (
    WorkflowPluginModel,
    WorkflowSpecModel,
)

LOG = logging.getLogger(__name__)

interface = "procflows"
family = "standard"
name = "order_based"


class OrderBased(BaseProcflowPlugin):
    """Execute an order-based process workflow (OBP).

    Loads a validated workflow specification, builds a ``Workflow``
    composite instance, and walks through steps in topological order,
    collecting output into an ``xr.DataTree``.
    """

    interface = "procflows"
    family = "order_based"
    name = "order_based"
    data_tree = True

    def call(
        self,
        workflow_spec: WorkflowPluginModel | WorkflowSpecModel | dict,
        fnames: Any,
        **kwargs: Any,
    ):
        """Run the order-based procflow.

        Parameters
        ----------
        workflow_spec : WorkflowPluginModel | WorkflowSpecModel | dict
            The workflow specification to execute.  May be a pre-validated
            model, a raw dictionary that will be validated on entry, or a
            ``WorkflowSpecModel`` that wraps a ``@spec:`` field.
        fnames : list[str] or str or None
            Input filename glob or list of filenames for reader steps.
        kwargs : dict
            Additional keyword arguments forwarded to the ``Workflow``.

        Returns
        -------
        xr.DataTree
            The fully-populated workflow DataTree.
        """
        if isinstance(workflow_spec, WorkflowSpecModel):
            wf_name = "embedded"
            spec = workflow_spec
        elif isinstance(workflow_spec, WorkflowPluginModel):
            wf_spec = workflow_spec
            wf_name = wf_spec.name
            spec = wf_spec.spec
        elif isinstance(workflow_spec, dict):
            ctx = {"skip_plugin_name_validation": True}
            if "spec" in workflow_spec and isinstance(workflow_spec["spec"], dict):
                wf_name = workflow_spec.get("name", "embedded")
                spec = WorkflowSpecModel.model_validate(
                    workflow_spec["spec"],
                    context=ctx,
                )
            else:
                wf_spec = WorkflowPluginModel.model_validate(
                    workflow_spec,
                    context=ctx,
                )
                wf_name = wf_spec.name
                spec = wf_spec.spec
        else:
            raise TypeError(
                f"Expected WorkflowPluginModel, WorkflowSpecModel, or "
                f"dict, got {type(workflow_spec).__name__}"
            )

        if isinstance(fnames, str):
            fnames = glob(fnames)

        LOG.interactive("Begin processing '%s' workflow.", wf_name)

        workflow = Workflow(spec, workflow_name=wf_name)
        result = workflow.call(fnames=fnames, **kwargs)

        LOG.interactive("The workflow '%s' has finished processing.", wf_name)
        return result


def call(workflow_spec, fnames, command_line_args=None, **kwargs):
    """Module-level entry point for pluginify discovery.

    Delegates to :class:`OrderBased.call`.
    """
    return OrderBased().call(
        workflow_spec,
        fnames=fnames,
        command_line_args=command_line_args,
        **kwargs,
    )


PLUGIN_CLASS = OrderBased
