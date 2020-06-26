from typing import Any, Dict, List, Tuple

from azureml.core import Workspace
from azureml.core.authentication import InteractiveLoginAuthentication
from azureml.core.compute import AmlCompute, ComputeTarget
from azureml.core.compute_target import ComputeTargetException
from azureml.pipeline.core import (
    Pipeline,
    PipelineEndpoint,
    Schedule,
    ScheduleRecurrence,
)
from azureml.pipeline.core._restclients.aeva.models.error_response import (
    ErrorResponseException,
)


def get_workspace(config):
    if "tenant_id" in config:
        # This part is only required, if you have access to multiple tenants (=Azure Active Directories), which is probably not the case.
        interactive_auth = InteractiveLoginAuthentication(tenant_id=config["tenant_id"])
        ws = Workspace.from_config(auth=interactive_auth)
    else:
        # This should suffice in the typical case.
        ws = Workspace.from_config()
    return ws


def get_or_create_compute(
    workspace: Workspace,
    compute_name: str,
    vm_size: str,
    min_nodes: int,
    max_nodes: int,
) -> ComputeTarget:
    try:
        return ComputeTarget(workspace=workspace, name=compute_name)
    except ComputeTargetException:
        compute_target = ComputeTarget.create(
            workspace,
            compute_name,
            AmlCompute.provisioning_configuration(
                vm_size=vm_size,
                vm_priority="lowpriority",
                min_nodes=min_nodes,
                max_nodes=max_nodes,
            ),
        )
        compute_target.wait_for_completion(show_output=True)
        return compute_target


def publish_pipeline(
    workspace: Workspace, steps: List, name: str, description: str = ""
) -> Tuple[str, PipelineEndpoint]:

    published_pipeline = Pipeline(workspace=workspace, steps=steps).publish(name)

    try:
        pipeline_endpoint = PipelineEndpoint.get(workspace, name=name)
        pipeline_endpoint.add_default(published_pipeline)
    except ErrorResponseException:
        pipeline_endpoint = PipelineEndpoint.publish(
            workspace, name=name, pipeline=published_pipeline, description=description
        )

    return published_pipeline.id, pipeline_endpoint


def create_or_update_schedule(
    workspace: Workspace,
    name: str,
    pipeline_id: str,
    experiment_name: str,
    recurrence: ScheduleRecurrence,
    pipeline_parameters: Dict[str, Any],
) -> Schedule:

    matching_schedules = [s for s in Schedule.list(workspace) if s.name == name]
    for s in matching_schedules:
        s.disable()

    return Schedule.create(
        workspace,
        name=name,
        pipeline_id=pipeline_id,
        experiment_name=experiment_name,
        recurrence=recurrence,
        pipeline_parameters=pipeline_parameters,
    )
