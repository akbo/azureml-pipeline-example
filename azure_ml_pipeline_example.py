import time

import requests
from azureml.core import RunConfiguration, Workspace
from azureml.core.conda_dependencies import CondaDependencies
from azureml.pipeline.core import Schedule, ScheduleRecurrence
from azureml.pipeline.core.graph import PipelineParameter
from azureml.pipeline.steps import PythonScriptStep

from aml_utils import (
    create_or_update_schedule,
    get_or_create_compute,
    get_workspace,
    publish_pipeline,
)
from config import ml_pipeline_test_config as config

ws = get_workspace(config)

compute_target = get_or_create_compute(ws, **config["compute"])

###
# Define and set up pipeline
###

pipeline_param = PipelineParameter(name="my_arg", default_value="default")

my_step = PythonScriptStep(
    name="My Script Step",
    script_name="scriptstep.py",
    arguments=[pipeline_param],
    inputs=[],
    outputs=[],
    compute_target=compute_target,
    source_directory="src",
    allow_reuse=True,
    runconfig=RunConfiguration(
        conda_dependencies=CondaDependencies(
            conda_dependencies_file_path="environment.yml"
        )
    ),
)

pipeline_id, pipeline_endpoint = publish_pipeline(ws, [my_step], "blabla")

###
# Trigger pipeline via REST API
###

# To trigger the pipeline, a service principal is required: https://docs.microsoft.com/en-us/azure/machine-learning/how-to-setup-authentication

token = requests.post(
    f"{config['sp']['resource_url']}/{config['sp']['tenant_id']}/oauth2/token",
    data={
        "grant_type": "client_credentials",
        "client_id": config["sp"]["client_id"],
        "client_secret": config["sp"]["client_secret"],
        "resource": "https://management.azure.com/",
    },
).json()["access_token"]

header = {
    "Authorization": "Bearer " + token,
    "Content-type": "application/json",
}

experiment_name = "requests_triggered"
trigger_response = requests.post(
    pipeline_endpoint.endpoint,
    headers=header,
    json={
        "ExperimentName": experiment_name,
        "ParameterAssignments": {"my_arg": "requests_triggered"},
    },
)

status_url = f"https://westeurope.api.azureml.ms/history/v1.0/subscriptions/{ws.subscription_id}/resourceGroups/{ws.resource_group}/providers/Microsoft.MachineLearningServices/workspaces/{ws.name}/experiments/{experiment_name}/runs/{trigger_response.json()['Id']}/details"
children_url = f"https://westeurope.api.azureml.ms/history/v1.0/subscriptions/{ws.subscription_id}/resourceGroups/{ws.resource_group}/providers/Microsoft.MachineLearningServices/workspaces/{ws.name}/experiments/{experiment_name}/runs/{trigger_response.json()['Id']}/children"

while True:
    status = requests.get(status_url, headers=header).json()["status"]
    print(status)
    if status == "Failed":
        break
    elif status == "Completed":
        break
    time.sleep(10)

###
# Schedule Pipeline
###

# More Info about ScheduleRecurrence: https://docs.microsoft.com/en-us/python/api/azureml-pipeline-core/azureml.pipeline.core.schedule.schedulerecurrence?view=azure-ml-py

recurrence = ScheduleRecurrence(
    frequency=config["schedule"]["frequency"], interval=config["schedule"]["interval"]
)

schedule = create_or_update_schedule(
    workspace=ws,
    name=config["schedule"]["name"],
    pipeline_id=pipeline_id,
    experiment_name=config["schedule"]["experiment_name"],
    recurrence=recurrence,
    pipeline_parameters={"my_arg": "schedule_triggered"},
)
