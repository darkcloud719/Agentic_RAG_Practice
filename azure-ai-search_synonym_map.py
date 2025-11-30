"""
FILE: azure-ai-search_synonym_map.py
DESCRIPTION:
    This sample demonstrates how to create, retrieve, and delete
    a synonym map in Azure AI Search using the Azure SDK for Python.
USAGE:
    python azure-ai-search_synonym_map.py
"""
import os, json, logging, sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.models import QueryType, QueryCaptionResult, QueryAnswerResult
from azure.search.documents.indexes.models import (
    SynonymMap,
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
    SemanticPrioritizedFields,
    SemanticSearch
)
from dotenv import load_dotenv
from typing import List
from rich import print as pprint

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")

def create_synonym_map():
    try:
        synonyms = [
            "USA, United States, United States of America",
            "Washington, Wash. => WA",
        ]

        synonym_map = SynonymMap(name="test-syn-map", synonyms=synonyms)
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.create_synonym_map(synonym_map)
            pprint(f"Synonym map '{result.name}' created successfully.")
    except Exception as ex:
        pprint(f"Error creating synonym map: {ex}")

def create_synonym_map_from_file():
    try:
        CWD = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(CWD, "synonym_map.json")
        with open(file_path, "r") as f:
            string_data = f.read()
            synonyms = string_data.splitlines("\n")
            synonym_map = SynonymMap(name="test-syn-map-file", synonyms=synonyms)
            with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
                result = search_index_client.create_synonym_map(synonym_map)
                pprint(f"Synonym map '{result.name}' created successfully from file.")
    except Exception as ex:
        pprint(f"Error creating synonym map from file: {ex}")

    
def get_synonym_maps():
    try:
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.get_synonym_maps()
            names = [x.name for x in result]
            pprint(f"Synonym maps: {names}")
    except Exception as ex:
        pprint(f"Error retrieving synonym maps: {ex}")

def get_synonym_map():
    try:
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.get_synonym_map("test-syn-map")
            pprint(f"Retrieved Synonym Map: {result.name}, Synonyms: {result.synonyms}")
    except Exception as ex:
        pprint(f"Error retrieving synonym map: {ex}")

def delete_synonym_map():
    try:
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.delete_synonym_map("test-syn-map")
            pprint(f"Synonym map deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting synonym map: {ex}")

if __name__ == "__main__":
    # create_synonym_map()
    get_synonym_maps()
    # get_synonym_map()
    # delete_synonym_map()