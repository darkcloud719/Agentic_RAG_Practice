from mcp.server import FastMCP
from neo4j import GraphDatabase
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery, QueryType
from dotenv import load_dotenv
from typing import List
import os, openai

load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "cve-vector-index"

openai.api_type = "azure"
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_API_ENDPOINT")

mcp_server = FastMCP("Search MCP Server", instructions="Provides data search services, including Graph Search and Vector Search")

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "P@ssw0rd"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@mcp_server.tool()
def graph_search(cve: str) -> dict:
    """PErform a graph search for the given CVE in Neo4j"""
# def neo4j_get_graph(tx, cve, hops=1):
    query = """
    MATCH (n)
    WHERE toLower(n.id) = toLower($cve)
    MATCH (n)-[r]-(m)
    RETURN n.id AS from, m.name AS to, type(r) AS relationship;
    """

    def fetch_triples(tx):
        res = tx.run(query, cve=cve)
        triples = []

        for row in res:
            f = row["from"]
            t = row["to"]
            rel = row["relationship"]
            triples.append(f"- {f} {rel} {t}")

        return triples

    with driver.session() as session:
        triples_text = session.execute_read(fetch_triples)

    return {
        "graph_search": triples_text
    }

@mcp_server.tool()
def vector_search(cve_description: str) -> dict:
    """Perform a vector search for the given CVE description in Azure AI Search"""
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
        
        all_records = [r for r in result]
        return {"vector_search":all_records}

if __name__ == "__main__":
    mcp_server.run(transport="stdio")