
import os
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient


STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "stsurveygenaidev01")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER", "survey-data")


def upload_etl_files():
    # Supports Azure CLI locally and configured cloud credentials.
    credential = DefaultAzureCredential()

    account_url = f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net"

    service_client = DataLakeServiceClient(
        account_url=account_url,
        credential=credential,
    )

    file_system_client = service_client.get_file_system_client(
        CONTAINER_NAME
    )

    project_folder = Path(__file__).resolve().parents[1]
    processed_folder = project_folder / "data" / "processed"

    files_to_upload = {
        "cleaned_responses.csv": "cleaned/cleaned_responses.csv",
        "invalid_responses.csv": "rejected/invalid_responses.csv",
        "quality_report.json": "quality-reports/quality_report.json",
    }

    uploaded_files = []

    for local_name, azure_path in files_to_upload.items():
        local_path = processed_folder / local_name

        if not local_path.is_file():
            raise FileNotFoundError(f"File not found: {local_path}")

        directory_name = azure_path.split("/")[0]
        directory_client = file_system_client.get_directory_client(
            directory_name
        )

        try:
            directory_client.create_directory()
        except ResourceExistsError:
            pass

        file_client = file_system_client.get_file_client(azure_path)

        with open(local_path, "rb") as file:
            file_client.upload_data(file, overwrite=True)

        uploaded_files.append(azure_path)

    return {
        "status": "success",
        "storage_account": STORAGE_ACCOUNT,
        "container": CONTAINER_NAME,
        "uploaded_files": uploaded_files,
    }
