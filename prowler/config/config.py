import os
import pathlib
import sys
from datetime import datetime, timezone
from os import getcwd

import requests
import yaml

from prowler.lib.logger import logger
from prowler.providers.common.common import get_global_provider

timestamp = datetime.today()
timestamp_utc = datetime.now(timezone.utc).replace(tzinfo=timezone.utc)
prowler_version = "4.0.1"
square_logo_img = "https://user-images.githubusercontent.com/38561120/235905862-9ece5bd7-9aa3-4e48-807a-3a9035eb8bfb.png"
aws_logo = "https://user-images.githubusercontent.com/38561120/235953920-3e3fba08-0795-41dc-b480-9bea57db9f2e.png"
azure_logo = "https://user-images.githubusercontent.com/38561120/235927375-b23e2e0f-8932-49ec-b59c-d89f61c8041d.png"
gcp_logo = "https://user-images.githubusercontent.com/38561120/235928332-eb4accdc-c226-4391-8e97-6ca86a91cf50.png"

orange_color = "\033[38;5;208m"
banner_color = "\033[1;92m"

finding_statuses = ["PASS", "FAIL", "MANUAL"]
valid_severities = ["critical", "high", "medium", "low", "informational"]

# Compliance
actual_directory = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))


def get_available_compliance_frameworks(provider=None):
    available_compliance_frameworks = []
    providers = ["aws", "gcp", "azure", "kubernetes"]
    if provider:
        providers = [provider]
    for provider in providers:
        with os.scandir(f"{actual_directory}/../compliance/{provider}") as files:
            for file in files:
                if file.is_file() and file.name.endswith(".json"):
                    available_compliance_frameworks.append(
                        file.name.removesuffix(".json")
                    )
    return available_compliance_frameworks


available_compliance_frameworks = get_available_compliance_frameworks()


# AWS services-regions matrix json
aws_services_json_file = "aws_regions_by_service.json"

# gcp_zones_json_file = "gcp_zones.json"

default_output_directory = getcwd() + "/output"
output_file_timestamp = timestamp.strftime("%Y%m%d%H%M%S")
timestamp_iso = timestamp.isoformat(sep=" ", timespec="seconds")
csv_file_suffix = ".csv"
json_file_suffix = ".json"
json_asff_file_suffix = ".asff.json"
json_ocsf_file_suffix = ".ocsf.json"
default_config_file_path = (
    f"{pathlib.Path(os.path.dirname(os.path.realpath(__file__)))}/config.yaml"
)


def get_default_mute_file_path(provider: str):
    """
    get_default_mute_file_path returns the default mute file path for the provider
    """
    # TODO: crate default mutelist file for kubernetes, azure and gcp
    if provider == "aws":
        return f"{pathlib.Path(os.path.dirname(os.path.realpath(__file__)))}/{provider}_mutelist.yaml"
    return None


def check_current_version():
    try:
        prowler_version_string = f"Prowler {prowler_version}"
        release_response = requests.get(
            "https://api.github.com/repos/prowler-cloud/prowler/tags", timeout=1
        )
        latest_version = release_response.json()[0]["name"]
        if latest_version != prowler_version:
            return f"{prowler_version_string} (latest is {latest_version}, upgrade for the latest features)"
        else:
            return (
                f"{prowler_version_string} (You are running the latest version, yay!)"
            )
    except requests.RequestException:
        return f"{prowler_version_string}"
    except Exception:
        return f"{prowler_version_string}"


# TODO: revisit this function
def update_provider_config(variable: str, value: str):
    try:
        global_provider = get_global_provider()
        if global_provider.audit_config and variable in global_provider.audit_config:
            global_provider.audit_config[variable] = value

    except Exception as error:
        logger.error(
            f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}] -- {error}"
        )


def load_and_validate_config_file(provider: str, config_file_path: str) -> dict:
    """
    load_and_validate_config_file reads the Prowler config file in YAML format from the default location or the file passed with the --config-file flag
    """
    try:
        with open(config_file_path) as f:
            config = {}
            config_file = yaml.safe_load(f)

            # Not to introduce a breaking change we have to allow the old format config file without any provider keys
            # and a new format with a key for each provider to include their configuration values within
            # Check if the new format is passed
            if "aws" in config_file or "gcp" in config_file or "azure" in config_file:
                config = config_file.get(provider, {})
            else:
                config = config_file if config_file else {}
                # Not to break Azure and GCP does not support neither use the old config format
                if provider in ["azure", "gcp"]:
                    config = {}

            return config

    except Exception as error:
        logger.critical(
            f"{error.__class__.__name__}[{error.__traceback__.tb_lineno}] -- {error}"
        )
        sys.exit(1)
