# import azure.functions as func
# import logging

# app = func.FunctionApp()

# # @app.function_name(name="HelloWorld")
# @app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
# def hello_world(req: func.HttpRequest) -> func.HttpResponse:
#     logging.info("HelloWorld function processed a request.")
#     return func.HttpResponse(
#         "Hello World",
#         status_code=200
#     )

import logging
import azure.functions as func
import json
import sys
import os
import time
from pydantic import BaseModel, validator, ValidationError
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
from azure.core.credentials import AzureKeyCredential
from typing import List
from rich import print as pprint
from dotenv import load_dotenv

load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class InitParams(BaseModel):
    index_name: str
    indexer_name: str
    container_name: str
    data_source_name: str
    skillset_name: str

    @validator("*")
    def check_none_and_empty(cls, v):
        
        if v is None:
            raise ValueError("Parameter is required")
        if isinstance(v, str) and not v.strip():
            raise ValueError("Parameter cannot be empty")
        
        return v
    
class InitResult(BaseModel):
    create_index:bool = False
    create_indexer:bool = False
    create_data_source:bool = False
    create_skillset:bool = False


class ResponseModel(BaseModel):
    code: int
    message: str
    data: InitResult | None = None

app = func.FunctionApp()

@app.route(route="Initialize", auth_level=func.AuthLevel.ANONYMOUS)
def Initialize(req: func.HttpRequest) -> func.HttpResponse:

    initial_result = InitResult()

    try:

        logging.info(f"parameters: {json.dumps(req.get_json(), indent=4)}")

        initial_params = InitParams.parse_obj(req.get_json())

        # initial_result = InitResult()

        search_client = SearchClient(endpoint=service_endpoint, index_name=initial_params.index_name, credential=AzureKeyCredential(key))
        search_index_client = SearchIndexClient(endpoint=service_endpoint, credential=AzureKeyCredential(key))
        search_indexer_client = SearchIndexerClient(endpoint=service_endpoint, credential=AzureKeyCredential(key))

        # if not _check_index_exists(initial_params.index_name, search_index_client):
        #     result = _create_index(initial_params.index_name, search_index_client)
        #     initial_result.create_index = True if result else False
        # else:
        #     initial_result.create_index = True


        # if not _check_data_source_exists(initial_params.data_source_name, search_indexer_client):
        #    result = _create_data_source_connection(initial_params.data_source_name, initial_params.container_name, search_indexer_client)
        #    initial_result.create_data_source = True if result else False

        # if not _check_skillset_exists(initial_params.skillset_name, search_indexer_client):
        #    result = _create_skillset(initial_params.skillset_name, search_indexer_client)
        #    initial_result.create_skillset = True if result else False

        initial_result.create_index = (True if _check_index_exists(initial_params.index_name, search_index_client) else bool(_create_index(initial_params.index_name, search_index_client)))
        initial_result.create_data_source = (True if _check_data_source_exists(initial_params.data_source_name, search_indexer_client) else bool(_create_data_source_connection(initial_params.data_source_name, initial_params.container_name, search_indexer_client)))
        initial_result.create_skillset = (True if _check_skillset_exists(initial_params.skillset_name, search_indexer_client) else bool(_create_skillset(initial_params.skillset_name, search_indexer_client)))
        

        if _check_indexer_exists(initial_params.indexer_name, search_indexer_client):
            result = _run_indexer(initial_params.indexer_name, search_indexer_client)
            initial_result.create_indexer = True if result else False
        else:
            if initial_params.index_name and initial_params.data_source_name and initial_params.skillset_name:
                result = _create_and_run_indexer(initial_params.indexer_name, initial_params.index_name, initial_params.data_source_name, initial_params.skillset_name, search_indexer_client)
                initial_result.create_indexer = True if result else False

    except Exception as ex:
        logging.error(f"Exception: {ex}")
        error_response = ResponseModel(code=400, message=str(ex), data=initial_result)
        error_json = json.dumps(error_response.dict(), indent=4)
        return func.HttpResponse(error_json, status_code=400, mimetype="application/json")
    
    success_response = ResponseModel(code=200, message="Initialization completed successfully.", data=initial_result)
    success_json = json.dumps(success_response.dict(), indent=4)
    return func.HttpResponse(success_json, status_code=200, mimetype="application/json")

            

    

def _create_index(index_name:str, search_index_client:SearchIndexClient) -> bool:
    try:
        fields = [
            SimpleField(name="hotelId", type=SearchFieldDataType.String, key=True, fitlerable=True, sortable=True),
            SimpleField(name="hotelName", type=SearchFieldDataType.String, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="description_fr", type=SearchFieldDataType.String, analyzer_name="fr.lucene"),
            SearchableField(name="category", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
            SearchableField(name="tags", type=SearchFieldDataType.String, facetable=True, filterable=True, collection=True),
            SimpleField(name="parkingIncluded", type=SearchFieldDataType.Boolean, filterable=True, sortable=True),
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
            )
        ]

        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="hotelName"),
                keywords_fields=[SemanticField(field_name="category"), SemanticField(field_name="tags")],
                content_fields=[SemanticField(field_name="description")]
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
        pprint(f"Error creating index {index_name}: {result}")

        return True
    
    except Exception as ex:
        pprint(f"Error creating index {index_name}: {ex}")
        return False

def _create_data_source_connection(data_source_name:str, container_name:str, search_indexer_client:SearchIndexerClient) -> bool:
    try:
        container = SearchIndexerDataContainer(name=container_name)

        data_source_connection = SearchIndexerDataSourceConnection(
            name=data_source_name,
            type="azureblob",
            connection_string=storage_connection_string,
            container=container
        )

        data_source = search_indexer_client.create_data_source_connection(data_source_connection)
        pprint(f"Data source connection {data_source_name} created successfully.")
        return True
    except Exception as ex:
        pprint(f"Error creating data source connection {data_source_name}: {ex}")
        return False
    
def _create_skillset(skillset_name:str, search_indexer_client:SearchIndexerClient) -> bool:
    try:
        inp = InputFieldMappingEntry(name="text", source="/document/description")

        sentiment_output = OutputFieldMappingEntry(name="sentiment", target_name="mysentiment")
        email_output = OutputFieldMappingEntry(name="emails", target_name="emails")
        name_output = OutputFieldMappingEntry(name="namedEntities", target_name="namedEntities")

        sentimentSkill = SentimentSkill(name="my-sentiment-skill", inputs=[inp], outputs=[sentiment_output])
        entityRecognitionSkill = EntityRecognitionSkill(name="my-entity-skill", inputs=[inp], outputs=[email_output, name_output])
        skillset = SearchIndexerSkillset(
            name=skillset_name,
            skills=[sentimentSkill, entityRecognitionSkill],
            description="Extract sentiment and named entities from hotel description"
        )

        result = search_indexer_client.create_skillset(skillset)

        pprint(f"Skillset '{skillset_name}' created successfully.")

        return True
    except Exception as ex:
        pprint(f"Error creating skillset {skillset_name}: {ex}")
        return False
    
def _create_and_run_indexer(indexer_name:str, index_name:str, data_source_name:str, skillset_name:str, search_indexer_client:SearchIndexerClient) -> bool:
    try:
        configuration = IndexingParametersConfiguration(
            parsing_mode="jsonArray",
            query_timeout=None
        )

        parameters = IndexingParameters(
            configuration=configuration
        )

        indexer = SearchIndexer(
            name=indexer_name,
            data_source_name=data_source_name,
            target_index_name=index_name,
            skillset_name=skillset_name,
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

        pprint(f"Indexer {indexer_name} created and run successfully.")

        return True
    
    except Exception as ex:

        pprint(f"Error creating indexer {indexer_name}: {ex}")

        return False
    
def _run_indexer(indexer_name:str, search_indexer_client:SearchIndexerClient) -> bool:
    try:
        search_indexer_client.run_indexer(indexer_name)
        pprint(f"Indexer {indexer_name} run successfully.")
        return True
    except Exception as ex:
        pprint(f"Error running indexer {indexer_name}: {ex}")
        return False

def _delete_index(index_name:str, search_index_client:SearchIndexClient) -> None:
    try:
        result = search_index_client.delete_index(index_name)
        pprint(f"Index {index_name} deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting index {index_name}: {ex}")

def _delete_data_source_connection(data_source_name:str, search_indexer_client:SearchIndexerClient) -> None:
    try:
        result = search_indexer_client.delete_data_source_connection(data_source_connection=data_source_name)
        pprint(F"Data source connection '{data_source_name}' deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting data source connection {data_source_name}: {ex}")

def _delete_skillset(skillset_name:str, search_indexer_client:SearchIndexerClient) -> None:
    try:
        result = search_indexer_client.delete_skillset(skillset=skillset_name)
        pprint(f"Skillset '{skillset_name}' deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting skillset {skillset_name}: {ex}")

def _delete_indexer(indexer_name:str, search_indexer_client:SearchIndexerClient) -> None:
    try:
        result = search_indexer_client.delete_indexer(indexer=indexer_name)
        pprint(f"Indexer '{indexer_name}' deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting indexer {indexer_name}: {ex}")

def _clear_index_documents_with_wait(index_name:str, search_client:SearchClient, batch_size=1000) -> None:
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

            time.sleep(2)

        pprint(f"All documents deleted from index {index_name} successfully. Total deleted: {total_deleted}")

    except Exception as ex:
        pprint(f"Error deleting documents from index {index_name}: {ex}")

def _check_index_exists(index_name:str, search_index_client:SearchIndexClient) -> bool:
    try:
        result = search_index_client.get_index(index_name)
        return True
    except Exception as ex:
        return False
    
def _check_data_source_exists(data_source_name:str, search_indexer_client:SearchIndexerClient) -> bool:
    try:
        result = search_indexer_client.get_data_source_connection(data_source_name)
        return True
    except Exception as ex:
        return False
    
def _check_skillset_exists(skillset_name:str, search_indexer_client:SearchIndexerClient) -> bool:
    try:
        result = search_indexer_client.get_skillset(skillset_name)
        return True
    except Exception as ex:
        return False
    
def _check_indexer_exists(indexer_name:str, search_indexer_client:SearchIndexerClient) -> bool:
    try:
        result = search_indexer_client.get_indexer(indexer_name)
        return True
    except Exception as ex:
        return False


    


        