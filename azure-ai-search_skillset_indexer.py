import os, json, logging, sys, time
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, QueryCaptionResult, QueryAnswerResult, VectorizedQuery
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer,
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    EntityRecognitionSkill,
    EntityRecognitionSkillVersion,
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
index_name = "hotels-vector-index"
indexer_name = "hotels-vector-indexer"
storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

search_client = SearchClient(endpoint=service_endpoint, index_name=index_name, credential=AzureKeyCredential(key))
search_index_client = SearchIndexClient(endpoint=service_endpoint, credential=AzureKeyCredential(key))
search_indexer_client = SearchIndexerClient(endpoint=service_endpoint, credential=AzureKeyCredential(key))

def _delete_index():
    try:
        result = search_index_client.delete_index(index_name)
        pprint(f"Index {index_name} deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting index: {index_name}:{ex}")

def _get_index():
    try:
        result = search_index_client.get_index(index_name)
        pprint(f"Index {index_name} retrieved successfully.")
    except Exception as ex:
        pprint(f"Error getting index: {index_name}:{ex}")
        

def _create_index():
    try:
        fields = [
            SimpleField(name="hotelId", type=SearchFieldDataType.String, key=True, filterable=True, sortable=True),
            SimpleField(name="hotelName", type=SearchFieldDataType.String, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="description_fr", type=SearchFieldDataType.String, analyzer_anme="fr.lucene"),
            SearchableField(name="category", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
            SearchableField(name="tags", type=SearchFieldDataType.String, facetable=True, filterable=True, collection=True),
            SimpleField(name="parkingIncluded", type=SearchFieldDataType.Boolean, filterable=True, sortable=True),
            SimpleField(name="smokingAllowed", type=SearchFieldDataType.Boolean, filterable=True, sortable=True),
            SimpleField(name="lastRenovationDate", type=SearchFieldDataType.DateTimeOffset, facetable=True, filterable=True, sortable=True),
            SimpleField(name="rating", type=SearchFieldDataType.Double, facetable=True, filterable=True, sortable=True),
            SimpleField(name="location", type=SearchFieldDataType.GeographyPoint, filterable=True, sortable=True),
            ComplexField(name="address", fields=[
                SearchableField(name="streetAddress", type=SearchFieldDataType.String),
                SearchableField(name="city", type=SearchFieldDataType.String, facetable=True, sortable=True),
                SearchableField(name="stateProvince", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="postalCode", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="country", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True)
            ]),
            SimpleField(name="url", type=SearchFieldDataType.String),
            SimpleField(name="file_name", type=SearchFieldDataType.String),
            SearchableField(name="emails", type=SearchFieldDataType.String, collection=True),
            SimpleField(name="mysentiment", type=SearchFieldDataType.String),
            ComplexField(
                name="namedEntities",
                fields=[
                    SimpleField(name="text", type=SearchFieldDataType.String),
                    SimpleField(name="category", type=SearchFieldDataType.String),
                    SimpleField(name="subcategory", type=SearchFieldDataType.String),
                    SimpleField(name="length", type=SearchFieldDataType.Int32),
                    SimpleField(name="offset", type=SearchFieldDataType.Int32),
                    SimpleField(name="confidenceScore", type=SearchFieldDataType.Double)
                ],
                collection=True
            ),
        ]

        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="hotelName"),
                keywords_fields=[SemanticField(field_name="category"), SemanticField(field_name="tags")],
                content_fields=[SemanticField(field_name="description"), SemanticField(field_name="description_fr")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"description":2.0})
        )

        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)

        suggester = [{"name":"sg","source_fields":["tags","address/city","address/country"]}]

        index = SearchIndex(
            name=index_name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            cors_options=cors_options,
            suggesters=suggester,
            semantic_search=semantic_search
        )

        result = search_index_client.create_index(index)

        pprint(f"Index {index_name} created successfully.")
    except Exception as ex:
        pprint(f"Error creating index: {index_name}:{ex}")


def _create_data_source_connection():
    try:
        container = SearchIndexerDataContainer(name="hotelscontainer")

        data_source_connection = SearchIndexerDataSourceConnection(
            name="hotels-datasource",
            type="azureblob",
            connection_string=storage_connection_string,
            container=container
        )

        data_source = search_indexer_client.create_data_source_connection(data_source_connection)
        pprint(f"data source connection 'hotels-datasource' created successfully.")
    except Exception as ex:
        pprint(f"Error creating data source connection: {ex}")


def _create_skillset():

    try:
        search_indexer_client.delete_skillset("hotels-skillset")

        inp = InputFieldMappingEntry(name="text", source="/document/description")

        sentiment_output = OutputFieldMappingEntry(name="sentiment", target_name="mysentiment")
        email_output = OutputFieldMappingEntry(name="emails", target_name="emails")
        name_output = OutputFieldMappingEntry(name="namedEntities", target_name="namedEntities")

        sentimentSkill = SentimentSkill(name="my-sentiment-skill", inputs=[inp], outputs=[sentiment_output]) 
        entityRecognitionSkill = EntityRecognitionSkill(name="my-entity-skill", inputs=[inp], outputs=[email_output, name_output])

        skillset = SearchIndexerSkillset(
            name="hotels-skillset",
            skills=[sentimentSkill, entityRecognitionSkill],
            description="Extract sentiment and named entities from hotel descriptions"
        )

        result = search_indexer_client.create_skillset(skillset)

        pprint(f"Skillset 'hotels-skillset' created successfully.")

    except Exception as ex:
        pprint(f"Error creating skillset: {ex}")

def _create_indexer():
    try:

        try:
            existing_indexer = search_indexer_client.get_indexer(indexer_name)
            pprint(f"Indexer '{indexer_name}' already exists. Running it now...")
            search_indexer_client.run_indexer(indexer_name)
            return
        except Exception:
            pprint(f"Indexer '{indexer_name}' does not exist. Creating it...")


        configuration = IndexingParametersConfiguration(
            parsing_mode="jsonArray",
            query_timeout=None
        )

        parameters = IndexingParameters(configuration=configuration)

        indexer = SearchIndexer(
            name=indexer_name,
            data_source_name="hotels-datasource",
            target_index_name=index_name,
            skillset_name="hotels-skillset",
            parameters=parameters,
            field_mappings=[
                FieldMapping(source_field_name="metadata_storage_path", target_field_name="url"),
                FieldMapping(source_field_name="metadata_storage_name", target_field_name="file_name")
            ],
            output_field_mappings=[
                FieldMapping(source_field_name="/document/mysentiment", target_field_name="mysentiment"),
                FieldMapping(source_field_name="/document/emails", target_field_name="emails"),
                FieldMapping(source_field_name="/document/namedEntities", target_field_name="namedEntities")
            ]
        )

        search_indexer_client.create_indexer(indexer)
        
        # search_indexer_client.run_indexer(indexer_name)

        pprint(f"Indexer {indexer_name} created and run successfully.")

    except Exception as ex:
        pprint(f"Error creating indexer: {ex}")

def _delete_indexer():
    try:
        search_indexer_client.delete_indexer(indexer_name)
        pprint(f"Indexer {indexer_name} deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting indexer: {indexer_name}:{ex}")

def _delete_data_source_connection():
    try:
        search_indexer_client.delete_data_source_connection("hotels-datasource")
        pprint(f"Data source connection 'hotels-datasource' deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting data source connection 'hotels-datasource':{ex}")


def _clear_index_documents_with_wait(batch_size=1000):
    try:
        total_deleted = 0

        while True:
            results = list(search_client.search(
                search_text="*",
                select=["hotelId"],
                top=batch_size
            ))

            if not results:
                break

            keys = [{"hotelId": doc["hotelId"]} for doc in results]

            search_client.delete_documents(documents=keys)

            total_deleted += len(keys)
            pprint(f"Deleted {len(keys)} documents...")

            time.sleep(2)

        pprint(f"All documents cleared. Total deleted: {total_deleted}")

    except Exception as ex:
        pprint(f"Error: {ex}")

if __name__ == "__main__":
    # _delete_index()
    # _delete_indexer()
    # _delete_data_source_connection()
    # _create_index()
    # _create_data_source_connection()
    # _create_skillset()
    # _create_indexer()
    _clear_index_documents_with_wait()

