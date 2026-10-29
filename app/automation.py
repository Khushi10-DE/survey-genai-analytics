
import os
import time

from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient

from app.azure_storage import upload_etl_files
from app.main import run_etl


RESOURCE_GROUP = os.getenv(
    "AZURE_RESOURCE_GROUP", "rg-survey-genai-dev"
)
FACTORY_NAME = os.getenv(
    "AZURE_DATA_FACTORY", "adf-survey-genai-dev"
)
PIPELINE_NAME = os.getenv(
    "AZURE_PIPELINE_NAME", "pl_survey_cleaned_to_analytics"
)


def run_automation():
    print("STEP 1: Running Google Sheets ETL...", flush=True)
    etl_result = run_etl()
    print(f"ETL completed: {etl_result}", flush=True)

    print("STEP 2: Uploading files to Azure...", flush=True)
    upload_result = upload_etl_files()
    print(f"Upload completed: {upload_result}", flush=True)

    print("STEP 3: Starting Azure Data Factory pipeline...", flush=True)

    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()

    adf_client = DataFactoryManagementClient(
        credential=credential,
        subscription_id=subscription_id,
    )

    pipeline_run = adf_client.pipelines.create_run(
        resource_group_name=RESOURCE_GROUP,
        factory_name=FACTORY_NAME,
        pipeline_name=PIPELINE_NAME,
    )

    run_id = pipeline_run.run_id
    print(f"ADF pipeline started. Run ID: {run_id}", flush=True)

    print("STEP 4: Waiting for ADF completion...", flush=True)

    timeout_seconds = 600
    polling_interval = 15
    start_time = time.monotonic()

    while time.monotonic() - start_time < timeout_seconds:
        run = adf_client.pipeline_runs.get(
            resource_group_name=RESOURCE_GROUP,
            factory_name=FACTORY_NAME,
            run_id=run_id,
        )

        print(f"ADF status: {run.status}", flush=True)

        if run.status == "Succeeded":
            print("FULL PIPELINE SUCCEEDED!", flush=True)
            return

        if run.status in ("Failed", "Cancelled"):
            raise RuntimeError(
                f"ADF pipeline {run.status}. Run ID: {run_id}"
            )

        time.sleep(polling_interval)

    raise TimeoutError(
        f"ADF pipeline did not finish within 600 seconds. Run ID: {run_id}"
    )


if __name__ == "__main__":
    run_automation()
