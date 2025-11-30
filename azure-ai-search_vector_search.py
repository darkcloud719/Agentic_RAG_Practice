"""
FILE: azure-ai-search_vector_search.py
DESCRIPTION:
    This sample demonstrates how to create, update, and search
    an index with vector search capabilities in Azure AI Search
    using the Azure SDK for Python.
USAGE:
    python azure-ai-search_vector_search.py
"""
import os, json, logging, sys, openai
from openai import AzureOpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient , SearchIndexingBufferedSender
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, QueryCaptionResult, QueryAnswerResult, VectorizedQuery, VectorizableTextQuery, VectorFilterMode
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
    SearchField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters
)
from typing import List
from rich import print as pprint

load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "azure-ai-service-vector-index"

openai.api_type = "azure"
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_API_ENDPOINT")

def delete_index():
    try:
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as index_client:
            index_client.delete_index(index_name)
            pprint(f"Index {index_name} deleted successfully.")
    except Exception as ex:
        pprint(f"Error deleting index {index_name}: {ex}")

def create_index():
    try:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="category", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="titleVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="myHnswProfile"
            ),
            SearchField(
                name="contentVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="myHnswProfile"
            )
        ]

        vector_search = VectorSearch(
            profiles=[VectorSearchProfile(name="myHnswProfile", algorithm_configuration_name="myHnsw")],
            algorithms=[HnswAlgorithmConfiguration(name="myHnsw")]
        )

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"content":1.5})
        )
        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        suggester = [{"name":"sg","source_fields":["title","content"]}]

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
            index = SearchIndex(
                name=index_name,
                fields=fields,
                cors_options=cors_options,
                vector_search=vector_search,
                semantic_search=semantic_search
            )

            result = search_index_client.create_index(index)
            pprint(f"Index {index_name} created successfully.")

    except Exception as ex:
        pprint(f"Error creating index {index_name}: {ex}")

def export_embeddings_to_json():

    try:
        path = os.path.join(os.path.dirname(__file__), "text-sample.json")
        with open(path, "r", encoding="utf-8") as file:
            input_data = json.load(file)

            titles = [item["title"] for item in input_data]
            content = [item["content"] for item in input_data]
            titles_response = openai.embeddings.create(input=titles, model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING"))
            title_embeddings = [item.embedding for item in titles_response.data]
            content_response = openai.embeddings.create(input=content, model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING"))
            content_embeddings = [item.embedding for item in content_response.data]

            for i, item in enumerate(input_data):
                title = item["title"]
                content = item["content"]
                item["titleVector"] = title_embeddings[i]
                item["contentVector"] = content_embeddings[i]

            output_path = os.path.join(os.path.dirname(__file__), "text-sample-with-embeddings.json")
            with open(output_path, "w", encoding="utf-8") as output_file:
                json.dump(input_data, output_file, ensure_ascii=False, indent=4)
    except Exception as ex:
        pprint(f"Error  exporting embeddings to json: {ex}")

def upload_documents():
    try:
        output_path = os.path.join(os.path.dirname(__file__), "text-sample-with-embeddings.json")

        with open(output_path, "r", encoding="utf-8") as file:
            documents = json.load(file)

        with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
            result = search_client.upload_documents(documents=documents)
            pprint(f"Uploaded {len(result)} documents to index {index_name}.")
    except Exception as ex:
        pprint(f"Error uploading documents to index {index_name}: {ex}")

def upload_documents_by_indexingbufferedsender():

    try:
        output_path = os.path.join(os.path.dirname(__file__), "text-sample-with-embeddings.json")
        with open(output_path, "r", encoding="utf-8") as file:
            documents = json.load(file)

        with SearchIndexingBufferedSender(
            endpoint=service_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        ) as batch_client:
            batch_client.upload_documents(documents=documents)
        
        pprint(f"Uploaded documents to index {index_name} using IndexingBufferedSender.")

    except Exception as ex:
        pprint(f"Error uploading documents using IndexingBufferedSender to index {index_name}: {ex}")


def search_documents_by_similarity():

    try:
        query = "tools for software development"
        embedding = openai.embeddings.create(
            input=query,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
        ).data[0].embedding

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=3,
            fields="contentVector"
        )

        # pprint(vector_query)

        with SearchClient(service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            result = search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["title","content","category"]
            )

            all_records = list(result)
            pprint(all_records)
    except Exception as ex:
        pprint(f"Error searching documents by similarity in index {index_name}: {ex}")

def search_documents_by_cross_fields():
    try:
        query = "tools for software development"
        embedding = openai.embeddings.create(
            input=query,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
        ).data[0].embedding

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=3,
            fields="titleVector,contentVector"
        )

        pprint(vector_query)

        with SearchClient(service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["title","content","category"]
            )

            all_records = list(results)
            pprint(all_records)
    except Exception as ex:
        pprint(f"Error searching documents by cross fields in index {index_name}: {ex}")

def search_documents_by_multi_vector():
    try:
        query1 = "tools for software development"
        query2 = "cloud computing platforms"

        embedding1 = openai.embeddings.create(
            input=query1,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
        ).data[0].embedding

        embedding2 = openai.embeddings.create(
            input=query2,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
        ).data[0].embedding

        vector_query1 = VectorizedQuery(
            vector=embedding1,
            k_nearest_neighbors=3,
            fields="titleVector"
        )

        vector_query2 = VectorizedQuery(
            vector=embedding2,
            k_nearest_neighbors=3,
            fields="contentVector"
        )

        with SearchClient(service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                search_text=None,
                vector_queries=[vector_query1, vector_query2],
                select=["title","content","category"],
                top=2
            )

            all_records = list(results)
            pprint(all_records)

    except Exception as ex:
        pprint(f"Errror searching documents by multi vector in index {index_name}: {ex}")

def hybrid_Search():

    try:
        query = "scalable storage solutions"

        embedding = openai.embeddings.create(
            input=query,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
        ).data[0].embedding

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=5,
            fields="contentVector"
        )

        with SearchClient(service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.SIMPLE,
                search_text=query,
                vector_queries=[vector_query],
                select=["title","content","category"],
                top=3
            )

            all_records = list(results)
            pprint(all_records)
    except Exception as ex:
        pprint(f"Error performing hybrid search in index {index_name}: {ex}")

def semantic_hybrid_search():

    try:
        query = "What is azure search ?"

        embedding = openai.embeddings.create(
            input=query,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
        ).data[0].embedding

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=5,
            fields="contentVector,titleVector"
        )

        with SearchClient(service_endpoint, index_name=index_name, credential=AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="my-semantic-config",
                query_caption=QueryCaptionType.EXTRACTIVE,
                query_answer=QueryAnswerType.EXTRACTIVE,
                search_text=query,
                vector_queries=[vector_query],
                select=["title","content","category"],
                top=1
            )

            all_records = list(results)
            pprint(all_records)

    except Exception as ex:
        pprint(f"Error performing semantic hybrid search in index {index_name}: {ex}")

if __name__ == "__main__":
    # delete_index()
    # create_index()
    # export_embeddings_to_json()
    # upload_documents()
    # search_documents_by_similarity()
    # search_documents_by_cross_fields()
    # search_documents_by_multi_vector()
    # hybrid_Search()
    semantic_hybrid_search()
