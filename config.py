ml_pipeline_test_config = {
    "compute": {
        "vm_size": "Standard_D1_v2",
        "compute_name": "ML-PIPELINE-TEST",
        "min_nodes": 0,
        "max_nodes": 1,
    },
    "sp": {
        "client_id": "...",
        "client_secret": "...",
        "resource_url": "https://login.microsoftonline.com",
        "tenant_id": "...",
    },
    "schedule": {
        "name": "TestSchedule",
        "experiment_name": "scheduled_test",
        "frequency": "Minute",
        "interval": 15,
    },
}
