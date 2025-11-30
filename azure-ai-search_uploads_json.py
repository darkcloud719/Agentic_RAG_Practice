"""
FILE: azure-ai-search_uploads_json.py
DESCRIPTION:
    This sample demonstrates how to create an index, and upload documents
    in JSON format to Azure AI Search using the Azure SDK for Python.
USAGE:
    python azure-ai-search_uploads_json.py
"""
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    CorsOptions,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    SearchIndex,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    ComplexField,
    ScoringProfile,
    TextWeights
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from typing import List
from rich import print as pprint
import os, json


load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "hotels-index"

def _create_index():
    
    try:
        
        fields = [
            SimpleField(name="hotelId", type=SearchFieldDataType.String, key=True),
            SearchableField(name="hotelName", type=SearchFieldDataType.String, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchableField(name="descriptionFr", type=SearchFieldDataType.String),
            SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="tags", type=SearchFieldDataType.String, facetable=True, filterable=True, collection=True),
            SimpleField(name="parkingIncluded", type=SearchFieldDataType.Boolean, filterable=True),
            SimpleField(name="smokingAllowed", type=SearchFieldDataType.Boolean, filterable=True),
            SimpleField(name="lastRenovationDate", type=SearchFieldDataType.DateTimeOffset, filterable=True),
            SimpleField(name="rating", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
            SimpleField(name="location", type=SearchFieldDataType.GeographyPoint, filterable=True),
            ComplexField(
                name="address",
                fields=[
                    SearchableField(name="streetAddress", type=SearchFieldDataType.String, filterable=True),
                    SearchableField(name="city", type=SearchFieldDataType.String, filterable=True),
                    SimpleField(name="stateProvince", type=SearchFieldDataType.String, filterable=True),
                    SimpleField(name="country", type=SearchFieldDataType.String, filterable=True),
                    SimpleField(name="postalCode", type=SearchFieldDataType.String, filterable=True)

                ]
            ),
            ComplexField(
                name="rooms",
                collection=True,
                fields=[
                    SearchableField(name="description", type=SearchFieldDataType.String),
                    SearchableField(name="descriptionFr", type=SearchFieldDataType.String),
                    SimpleField(name="type", type=SearchFieldDataType.String),
                    SimpleField(name="baseRate", type=SearchFieldDataType.Double),
                    SimpleField(name="bedOptions", type=SearchFieldDataType.String),
                    SimpleField(name="sleepsCount", type=SearchFieldDataType.Int32),
                    SimpleField(name="smokingAllowed", type=SearchFieldDataType.Boolean),
                    SearchableField(name="tags", type=SearchFieldDataType.String, collection=True)
                ]
            )
        ]

        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"description":2.0, "hotelName":1.5})
        )
        scoring_profiles.append(scoring_profile)

        index = SearchIndex(
            name=index_name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            cors_options=cors_options
        )

        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.create_index(index)

        pprint(f"Index {index_name} created successfully.")

    except Exception as ex:
        pprint(f"Error creating index {index_name}: {ex}")

def _delete_index():
    
    try:
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as index_client:
            index_client.delete_index(index_name)
            pprint(f"Index {index_name} deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting index {index_name}: {ex}")

def _upload_documents():

    try:
        path = os.path.join(os.path.dirname(__file__), "hotels-small.json")

        with open(path, "r", encoding="utf-8") as file:
            input_data = json.load(file)
            with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
                result = search_client.upload_documents(documents=input_data)
                pprint(f"Uploaded {len(result)} documents to index {index_name}.")

    except Exception as ex:
        pprint(f"Error uploading documents to index {index_name}: {ex}")

    
if __name__ == "__main__":
    _delete_index()
    _create_index()
    _upload_documents()
