"""Unit tests for GeoipsWorkflowCommand.workflow_type input classification."""

import pytest

from geoips.commandline import geoips_command


class DummyParser:
    """Small parser stub that makes parser.error test-visible."""

    def error(self, message):
        """Raise an assertion so parser errors fail the test."""
        raise AssertionError(message)


class FakeWorkflowPluginModel:
    """Model stub that preserves constructor arguments."""

    def __init__(self, **kwargs):
        """Store keyword arguments supplied to the model stub."""
        self.kwargs = kwargs

    def model_dump(self):
        """Return the stored keyword arguments like a pydantic model."""
        return self.kwargs


class WorkflowCommandForTest(geoips_command.GeoipsWorkflowCommand):
    """Concrete test shell for the abstract workflow command."""

    name = "workflow_type_test"
    command_classes = []

    def add_arguments(self):
        """Satisfy the abstract command API for tests."""
        pass

    def __call__(self, args):
        """Satisfy the abstract command API for tests."""
        pass


@pytest.fixture
def workflow_command(monkeypatch):
    """Return a GeoipsWorkflowCommand instance with external validation mocked."""
    monkeypatch.setattr(
        geoips_command, "WorkflowPluginModel", FakeWorkflowPluginModel
    )
    command = object.__new__(WorkflowCommandForTest)
    command.parser = DummyParser()
    return command


def test_workflow_type_loads_yaml_path_before_registered_name_lookup(
    monkeypatch, tmp_path, workflow_command
):
    """A YAML filepath should be loaded as an unregistered workflow."""
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        "\n".join(
            [
                "apiVersion: geoips/v1",
                "interface: workflows",
                "family: order_based",
                "name: path_workflow",
                "spec: {}",
            ]
        )
    )

    def fail_get_plugin(*args, **kwargs):
        pytest.fail("YAML workflow path was treated as a registered plugin name")

    monkeypatch.setattr(geoips_command.workflows, "get_plugin", fail_get_plugin)

    workflow = workflow_command.workflow_type(str(workflow_path))

    assert workflow["name"] == "path_workflow"
    assert workflow["is_registered"] is False
    assert workflow["context"] == {"expand": True}


def test_workflow_type_accepts_registered_workflow_names(
    monkeypatch, workflow_command
):
    """A non-path string should still resolve through the workflow registry."""
    calls = []

    def fake_get_plugin(*args, **kwargs):
        calls.append((args, kwargs))
        return {"name": args[0], "registered": True}

    monkeypatch.setattr(geoips_command.workflows, "get_plugin", fake_get_plugin)

    workflow = workflow_command.workflow_type("registered_workflow")

    assert workflow == {"name": "registered_workflow", "registered": True}
    assert calls[0][0] == ("registered_workflow",)
    assert calls[0][1]["_expand"] is True
    assert "rebuild_registries" in calls[0][1]


def test_workflow_type_accepts_direct_dicts(workflow_command):
    """Programmatic dict inputs should be validated as unregistered workflows."""
    workflow = workflow_command.workflow_type(
        {
            "apiVersion": "geoips/v1",
            "interface": "workflows",
            "family": "order_based",
            "name": "dict_workflow",
            "spec": {},
        }
    )

    assert workflow["name"] == "dict_workflow"
    assert workflow["is_registered"] is False
    assert workflow["context"] == {"expand": True}
