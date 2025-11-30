import os, json, logging, sys, openai
from openai import AzureOpenAI
from dotenv import load_dotenv
from tenacity import retry, wait_fixed, stop_after_attempt, wait_random_exponential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient, SearchIndexingBufferedSender
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, QueryCaptionResult, QueryAnswerResult, VectorizedQuery
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
index_name = "cve-vector-index"

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
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="cveId", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchableField(name="vendor", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="product", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="version", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="cvssScore", type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SearchField(
                name="descriptionVector",
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
            text_weights=TextWeights(weights={"description":2})
        )
        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        
        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                # title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="cveId")],
                content_fields=[SemanticField(field_name="description")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            index = SearchIndex(
                name=index_name,
                fields=fields,
                cors_options=cors_options,
                vector_search=vector_search,
                # semantic_search=semantic_search
            )

            result = search_index_client.create_index(index)
            pprint(f"Index {index_name} created successfully.")

    except Exception as ex:
        pprint(f"Error creating index {index_name}: {ex}")

def parse_cve_json(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        cveId = data["cveMetadata"]["cveId"]
        cna = data["containers"]["cna"]

        description = ""
        if "descriptions" in cna and len(cna["descriptions"]) > 0:
            description = cna["descriptions"][0].get("value","")

        vendor = product = version = ""

        affected_list = cna.get("affected", [])
        if affected_list:
            vendor = affected_list[0].get("vendor","")
            product = affected_list[0].get("product","")

            version_list = affected_list[0].get("versions", [])
            if version_list:
                version = version_list[0].get("lessThan", version_list[0].get("version",""))

        cvssScore = None
        metrics_list = cna.get("metrics", [])
        if metrics_list:
            cvssScore = metrics_list[0].get("cvssV3_1", {}).get("baseScore", None)

        return {
            "cveId": cveId,
            "description": description,
            "vendor": vendor,
            "product": product,
            "version": version,
            "cvssScore": cvssScore
        }
    except Exception as ex:
        pprint(f"Error parsing CVE JSON file {path}: {ex}")


def import_all_cve(folder):
    try:
        files = [f for f in os.listdir(folder) if f.endswith(".json")]
        pprint(f"[cyan]Found {len(files)} JSON files[/cyan]")

        docs = []

        # for file_name in files:
        for i, file_name in enumerate(files, start=1):
            path = os.path.join(folder, file_name)
            pprint(f"[yellow]Processing {file_name}...[/yellow]")

            doc = parse_cve_json(path)
            doc["id"] = str(i)
            docs.append(doc)

        description_list = [doc["description"] for doc in docs]
        # description_list = [doc["description"] for doc in docs if doc["description"].strip() != ""]

        # pprint(description_list)
        # description_embeddings = openai.embeddings.create(input=description_list, model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING"))

        for i, item in enumerate(docs):
            # pprint(description_embeddings.data[i])
            # item["descriptionVector"] = description_embeddings.data[i].embedding
            if item["description"].strip() != "":
                embedding_response = openai.embeddings.create(
                    input=item["description"],
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
                )
                item["descriptionVector"] = embedding_response.data[0].embedding

        with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
            search_client.upload_documents(documents=docs)       
            pprint(f"[green]Uploaded {len(docs)} documents to index {index_name}[/green]")
    except Exception as ex:
        pprint(f"Error importing CVE data: {ex}")

def query_vector_search(cve_description):
    try:

        embedding_response = openai.embeddings.create(
            input=cve_description,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
        )

        query_vector=embedding_response.data[0].embedding
        
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=2,
            fields="descriptionVector"
        )

        with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
            result = search_client.search(
                query_type=QueryType.SIMPLE,
                search_text=cve_description,
                vector_queries=[vector_query],
                select=["cveId","description","vendor","product","version","cvssScore"],
                top=2
            )

            all_records = list(result)
            pprint(all_records)
    except Exception as ex:
        pprint(f"Error querying vector search: {ex}")
    
if __name__ == "__main__":
    # delete_index()
    # create_index()

    # folder = os.path.join(os.path.dirname(__file__), "2025")
    # import_all_cve(folder)
    # pprint("[green]All CVE files imported to Azure AI Search![/green]")

    # query_vector_search("Buffer Overflow in ProductX version 1.2 allows remote attackers to execute arbitrary code.")
    query_vector_search("What are the CVEs related to Chrome?")