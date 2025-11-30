"""
FILE: azure-ai-search_datasource.py
DESCRIPTION:
    This sample demonstrates how to create, list, get, and delete
    a data source connection in Azure Cognitive Search using the Azure SDK for Python.
USAGE:
    python azure-ai-search_datasource.py
"""
import os, json, logging, sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.models import QueryType, QueryCaptionResult, QueryAnswerResult
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer,
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchIndexerSkillset,
    SearchableField,
    IndexingParameters,
    SearchIndexerDataSourceConnection,
    IndexingParametersConfiguration,
    IndexingSchedule,
    CorsOptions,
    SearchIndexer,
    FieldMapping,
    ScoringProfile,
    ComplexField,
    TextWeights,
    SearchField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch
)
from dotenv import load_dotenv
from typing import List
from rich import print as pprint

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

def create_data_source_connection():
    try:
        container = SearchIndexerDataContainer(name="mycontainer3")
        data_source_connection = SearchIndexerDataSourceConnection(
            name="my-azure-blob-datasource",
            type="azureblob",
            connection_string=connection_string,
            container=container
        )

        with SearchIndexerClient(service_endpoint, credential=AzureKeyCredential(key)) as indexer_client:
            result = indexer_client.create_data_source_connection(data_source_connection)
            pprint(f"Data source connection created: {result.name}")
    except Exception as ex:
        pprint(f"Error creating data source connection: {ex}")

def list_data_source_connections():
    try:
        with SearchIndexerClient(service_endpoint, credential=AzureKeyCredential(key)) as indexer_client:
            result = indexer_client.get_data_source_connections()
            names = [ds.name for ds in result]
            pprint(f"Data source connections: {names}")
    except Exception as ex:
        pprint(f"Errror listing data source connections: {ex}")

def get_data_source_connection():
    try:
        with SearchIndexerClient(service_endpoint, credential=AzureKeyCredential(key)) as indexer_client:
            result = indexer_client.get_data_source_connection("my-azure-blob-datasource")
            pprint(f"Retrieved Data Source Connection: {result.name}")
    except Exception as ex:
        pprint(f"Error retrieving data source connection: {ex}")

def delete_data_source_connection():
    try:
        with SearchIndexerClient(service_endpoint, credential=AzureKeyCredential(key)) as indexer_client:
            result = indexer_client.delete_data_source_connection("sample-data-source")
            pprint(result)
            pprint(f"Data source connection deleted.")
    except Exception as ex:
        pprint(f"Error deleting data source connection: {ex}")

if __name__ == "__main__":
    create_data_source_connection()
    # list_data_source_connections()
    # get_data_source_connection()
    # delete_data_source_connection()



