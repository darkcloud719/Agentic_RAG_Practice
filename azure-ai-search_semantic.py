"""
FILE: azure-ai-search_semantic.py
DESCRIPTION:
    This sample demonstrates how to create, update, and search
    an index with semantic search capabilities in Azure Cognitive Search
    using the Azure SDK for Python.
USAGE:
    python azure-ai-search_semantic.py
"""
import os, json, logging, sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.models import QueryType, QueryCaptionResult, QueryAnswerResult, QueryAnswerResult
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "azure-ai-service-index"

def _delete_index():
    try:
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.delete_index(index_name)
            pprint(f"Index {index_name} deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting index {index_name}: {ex}")

def _create_index():
    try:
        fields = [
            SimpleField(name="Id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="category", type=SearchFieldDataType.String)
        ]

        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="category")],
                content_fields=[SemanticField(field_name="content")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(name="MyProfile", text_weights=TextWeights(weights={"content":1.5}))
        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        suggester = [{"name":"sg","source_fields":["title","content"]}]

        index = SearchIndex(
            name=index_name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            cors_options=cors_options,
            semantic_search=semantic_search
        )

        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.create_index(index)
            print(f"Index {index_name} created successfully.")
    except Exception as ex:
        pprint(f"Error creating index {index_name} : {ex}")

def _update_index():
    try:
        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="category")],
                content_fields=[SemanticField(field_name="content")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            index = search_index_client.get_index(index_name)
            index.semantic_search = semantic_search
            result = search_index_client.create_or_update_index(index)
            pprint(f"Index {index_name} updated successfully.")
    except Exception as ex:
        pprint(f"Error updating index {index_name}: {ex}")

def _upload_documents():
    try:
        path = os.path.join(os.path.dirname(__file__), "text-sample.json")
        with open(path, "r", encoding="utf-8") as file:
            input_data = json.load(file)
            with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
                result = search_client.upload_documents(documents=input_data)
                pprint(f"Uploaded {len(result)} documents to index {index_name}.")
    except Exception as ex:
        pprint(f"Error uploading documents to index {index_name}: {ex}")

def search_index_by_querytype_semantic():
    try:
        with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.SEMANTIC,
                search_text="gateway",
                include_total_count=True,
                semantic_configuration_name="my-semantic-config"
            )

            all_records = list(results)

            pprint(all_records)

    except Exception as ex:
        pprint(f"Error searching index {index_name} by semantic query type: {ex}")

if __name__ == "__main__":
    # _delete_index()
    # _create_index()
    # _upload_documents()
    # _update_index()
    search_index_by_querytype_semantic()


