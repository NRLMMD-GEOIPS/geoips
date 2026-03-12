# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Processing workflow for order based data source processing."""

# Python Standard Libraries
from argparse import ArgumentParser
import logging

# GeoIPS imports
from geoips import interfaces
from geoips.pydantic.workflows import WorkflowPluginModel

LOG = logging.getLogger(__name__)

interface = "procflows"
family = "standard"
name = "order_based"

ef validate_workflow_file_inputs(wf, fnames):
    """Validate that all required file inputs exist before processing begins.
 
    Iterates over the workflow steps and checks that file paths required by
    ``reader``, ``output_checker``, and ``sector`` steps are accessible on the
    filesystem. If any paths are missing, the workflow is terminated with an
    actionable error message listing every missing file and the step that
    requires it.
 
    Parameters
    ----------
    wf : WorkflowPluginModel
        The fully constructed workflow plugin model whose steps will be
        inspected.
    fnames : list of str
        List of input filenames provided on the command line for reader steps.
 
    Raises
    ------
    FileNotFoundError
        If one or more required file paths do not exist. The error message
        enumerates each missing path alongside the step ID and step kind that
        requires it.
    """
    missing = []
 
    # Validate command-line fnames shared by all reader steps.
    for path in fnames:
        if not os.path.exists(path):
            missing.append(("command_line_args", "reader", path))
 
    for step_id, step_def in wf.spec.steps.items():
        if step_def.kind == "output_checker":
            _validate_output_checker_files(step_id, step_def, missing)
        elif step_def.kind == "sector":
            _validate_sector_files(step_id, step_def, missing)
 
    if missing:
        error_lines = [
            "The workflow cannot proceed because the following required "
            "file(s) were not found:"
        ]
        for step_id, kind, path in missing:
            error_lines.append(f"  step '{step_id}' (kind: {kind}): {path}")
 
        raise FileNotFoundError("\n".join(error_lines))
 
 
def _validate_output_checker_files(step_id, step_def, missing):
    """Check that the comparison path for an output_checker step exists.
 
    If ``compare_path`` is present and non-null in the step's arguments, its
    existence on the filesystem is verified. A null or absent ``compare_path``
    is not flagged here; logical consistency between ``checker_name`` and
    ``compare_path`` is already enforced by
    ``OutputCheckersArgumentsModel``.
 
    Parameters
    ----------
    step_id : str
        The identifier of the workflow step being validated.
    step_def : WorkflowStepDefinitionModel
        The step definition whose arguments may contain a ``compare_path``.
    missing : list of tuple
        Accumulator for ``(step_id, kind, path)`` entries describing missing
        files. Modified in place.
    """
    compare_path = step_def.arguments.get("compare_path", None)
    if compare_path is None:
        return
 
    if not os.path.exists(compare_path):
        missing.append((step_id, "output_checker", compare_path))
 
 
def _validate_sector_files(step_id, step_def, missing):
    """Check that file paths in a sector step's arguments exist.
 
    Sector steps may reference ancillary input files via an ``fnames`` key in
    their arguments. Each path in that list is checked for existence on the
    filesystem.
 
    Parameters
    ----------
    step_id : str
        The identifier of the workflow step being validated.
    step_def : WorkflowStepDefinitionModel
        The step definition whose arguments may contain an ``fnames`` list.
    missing : list of tuple
        Accumulator for ``(step_id, kind, path)`` entries describing missing
        files. Modified in place.
    """
    sector_fnames = step_def.arguments.get("fnames", None)
    if sector_fnames is None:
        return
 
    for path in sector_fnames:
        if not os.path.exists(path):
            missing.append((step_id, "sector", path))
 

def call(workflow, fnames, command_line_args=None):
    """Run the order based procflow (OBP).

    Process the specified input data files using the OBP in the order of steps
    listed in the workflow definition file.

    Parameters
    ----------
    workflow: str
        The name of the workflow to process.
    fnames : list of str
        List of filenames from which to read data.
    command_line_args : list of str, None
        Command line arguments to pass to the workflow.
    """
    LOG.interactive(f"Begin processing '{workflow}' workflow.")
    wf_plugin = interfaces.workflows.get_plugin(workflow)
    wf = WorkflowPluginModel(**wf_plugin)

    validate_workflow_file_inputs(wf, fnames)

    handled_interfaces = ["readers"]
    for step_id, step_def in wf.spec.steps.items():
        interface = step_def.kind + "s"

        if interface not in handled_interfaces:
            LOG.interactive(
                "⚠️ Skipping unhandled interface '%s'. Would have called the '%s'"
                "plugin.",
                interface,
                step_def.name,
            )
            continue
        else:
            plg = getattr(interfaces, interface, None).get_plugin(step_def.name)
            LOG.interactive(
                "Beginning Step: '%s', plugin_kind: '%s', plugin_name:'%s'.",
                step_id,
                step_def.kind,
                step_def.name,
            )
            LOG.info("Arguments: '%s'", step_def.arguments)

            if interface == "readers":
                # TEMPORARY FIX: Remove when all readers are updated to accept
                # "variables"
                if "variables" in step_def.arguments:
                    step_def.arguments["chans"] = step_def.arguments.pop("variables")
                data = plg(fnames, **step_def.arguments)
                print(data)
            else:
                data = plg(data, **step_def.arguments)
            LOG.interactive(
                "Completed Step: step_id: '%s', plugin_kind: '%s', plugin_name: '%s'.",
                step_id,
                step_def.name,
                step_def.kind,
            )

    LOG.interactive(f"\nThe workflow '{workflow}' has finished processing.\n")


if __name__ == "__main__":

    parser = ArgumentParser(description="order-based procflow processing")
    parser.add_argument("workflow", help="The workflow name to process.")
    parser.add_argument("fnames", nargs="+", help="The filenames to process.")
    args = parser.parse_args()
    call(args.workflow, args.fnames)
