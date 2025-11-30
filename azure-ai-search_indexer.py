"""
FILE: azure-ai-search-indexer.py
DESCRIPTION:
    This sample demonstrates how to create, update, and use
    an indexer in Azure Cognitive Search using the Azure SDK for Python.
USAGE:
    python azure-ai-search-indexer.py
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
    EntityRecognitionSkill,
    SentimentSkill,
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
    ImageAnalysisSkill,
    OcrSkill,
    VisualFeature,
    TextWeights,
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
indexer_name = "azure-ai-service-indexer"
data_source_name = "azure-ai-service-datasource"
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

def _delete_index():
    try:
        with SearchIndexClient(endpoint=service_endpoint, credential=AzureKeyCredential(key)) as index_client:
            index_client.delete_index(index_name)
            pprint(f"Index {index_name} deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting index {index_name}: {ex}")

def _create_index():
    try:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="category", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="content", type=SearchFieldDataType.String)
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
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"content":1.5})
        )

        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        suggester = [{"name":"sg","source_fields":["title","content"]}]

        index = SearchIndex(
            name=index_name,
            fields=fields,
            cors_options=cors_options,
            scoring_profiles=scoring_profiles
        )

        with SearchIndexClient(endpoint=service_endpoint, credential=AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.create_index(index)
            pprint(f"Index {index_name} created successfully.")
    except Exception as ex:
        pprint(f"Error creating index {index_name}: {ex}")

def _create_data_source_connection():
    try:
        container = SearchIndexerDataContainer(name="mycontainer3")

        data_source_connection = SearchIndexerDataSourceConnection(
            name=data_source_name,
            type="azureblob",
            connection_string=connection_string,
            container=container
        )

        with SearchIndexerClient(endpoint=service_endpoint, credential=AzureKeyCredential(key)) as indexer_client:
            indexer_client.create_data_source_connection(data_source_connection)
            pprint(f"Data source connection {data_source_name} created successfully.")
    except Exception as ex:
        pprint(f"Error creating data source connection: {ex}")

def _create_indexer():
    try:
        configuration = IndexingParametersConfiguration(
            parsing_mode="jsonArray",
            query_timeout=None
        )

        parameters = IndexingParameters(configuration=configuration)

        indexer = SearchIndexer(
            name=indexer_name,
            data_source_name=data_source_name,
            target_index_name=index_name,
            parameters=parameters
        )

        with SearchIndexerClient(endpoint=service_endpoint, credential=AzureKeyCredential(key)) as indexer_client:
            indexer_client.create_indexer(indexer)
            pprint(f"Indexer {indexer_name} created successfully.")

    except Exception as ex:
        pprint(f"Error creating indexer {indexer_name}: {ex}")

def _simple_query_search():
    try:
        with SearchClient(endpoint=service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.SIMPLE,
                search_fields=["title"],
                search_text="Azure",
                include_total_count=True,
                scoring_profile="MyProfile",
                top=5
            )

            pprint(f"Total results: {results.get_count()}")
            
            all_results = list(results)
            pprint(all_results)

    except Exception as ex:
        pprint(f"Error performing simple query search: {ex}")


def _full_query_search():
    try:
        with SearchClient(endpoint=service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.FULL,
                search_text="title:'Azure' AND category:'Management'",
                include_total_count=True
            )

            pprint(f"Total results: {results.get_count()}")

            all_results = list(results)
            pprint(all_results)

            for result in results:
                for result_key, value in result.items():
                    pprint(f"{result_key}:{value}")
                print("\n\n")

    except Exception as ex:
        pprint(f"Error performing full query search: {ex}")

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

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"content":1.5})
        )

        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        suggester = [{"name":"sg","source_fields":["title","content"]}]

        with SearchIndexClient(endpoint=service_endpoint, credential=AzureKeyCredential(key)) as search_index_client:
            index = search_index_client.get_index(index_name)
            index.semantic_search = semantic_search
            index.cors_options = cors_options
            index.scoring_profiles = scoring_profiles
            # index.suggesters = suggester

            result = search_index_client.create_or_update_index(index)

    except Exception as ex:
        pprint(f"Error updating index {index_name}: {ex}")

def _semantic_query_search():
    try:
        with SearchClient(endpoint=service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.SEMANTIC,
                search_text="Who is Nick?",
                include_total_count=True,
                semantic_configuration_name="my-semantic-config",
                query_caption="extractive",
                query_answer="extractive",
                top=2
            )

            pprint(f"Total results: {results.get_count()}")

            all_results = list(results)

            pprint(all_results)

    except Exception as ex:
        pprint(f"Error performing semantic query search: {ex}")

if __name__ == "__main__":
    # _delete_index()
    # _create_index()
    # _create_data_source_connection()
    # _create_indexer()
    # _simple_query_search()
    # _full_query_search()
    # _update_index()
    _semantic_query_search()