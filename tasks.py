from pprint import pprint

from azureml.core import Workspace
from azureml.core.compute import AmlCompute
from azureml.pipeline.core import PipelineEndpoint, PublishedPipeline, Schedule
from invoke import task


@task
def clean_azml_workspace(ctx):
    """
    [WARNING] Only use in test-only workspace. Remove or disable all compute clusters, published pipelines, published pipeline endpoints and schedules from Azure ML workspace.
    """

    ws = Workspace.from_config()

    # remove compute clusters
    for _, compute in ws.compute_targets.items():
        if not compute.provisioning_state == "Deleting":
            compute.delete()

    # deactivate schedules
    for s in Schedule.list(ws):
        s.disable()

    # remove pipeline endpoints
    for pe in PipelineEndpoint.list(ws):
        pe.disable()

    # remove pipelines
    for p in PublishedPipeline.list(ws):
        p.disable()


@task
def show_available_vm_sizes(ctx):
    """
    Show, which VM Sizes are available in the workspace's Azure region
    """

    ws = Workspace.from_config()

    pprint(AmlCompute.supported_vmsizes(workspace=ws))

    print(
        "\n>>> For VM prices, see https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/ <<<\n"
    )
