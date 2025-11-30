import os
import json
import openai
from azure.core.credentials import AzureKeyCredential
from neo4j import GraphDatabase
from dotenv import load_dotenv
from rich import print as pprint

load_dotenv()

openai.api_type = "azure"
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_API_ENDPOINT")

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "P@ssw0rd"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

GRAPH_EXTRACTION_PROMPT = """
-Goal-
Given any arbitrary text document, extract meaningful entities and their relationships
and return a structured JSON object suitable for direct Neo4j import.

-Important Rules-
1. Do NOT invent facts that are not present in the text.
2. Infer entities and relationships only when strongly supported by the text.
3. Capitalization rules:
   - Entity "name": Only capitalize the first letter of each word.
   - Entity "type": Only capitalize the first letter. Use: Person, Organization, Location, Product, Event, Project, Other.
   - Relationship fields "source", "target", "relationship": Only capitalize the first letter.
4. Avoid merging separate entities with similar names.
5. Keep descriptions concise and factual.

-Steps-
1. Identify all important entities in the text.
   For each entity, produce:
   - "name": Proper-case capitalization ("Sam Altman", "Contoso Corp", "GlobalTech").
   - "type": One of: Person, Organization, Location, Product, Event, Project, Other.
   - "description": A concise description from the text.

2. Identify all relationships between entities.
   For each relationship, produce:
   - "source": Name of the source entity (proper-case).
   - "target": Name of the target entity (proper-case).
   - "relationship": A verb/action describing the relationship (e.g., WorksAt, Founded, AcquiredBy, CollaboratesWith).
   - "description": Explanation of the relationship.
   - "strength": A numeric score (1–10) for relationship strength.

3. Return the final JSON structure:
{
  "entities": [...],
  "relationships": [...]
}

-Output Format Rules-
- Only output pure JSON.
- Do not output explanation text.
- Do not output empty arrays unless necessary.
- Ensure the JSON is valid.

-Example Output Format-
{
  "entities": [
    {
      "name": "Alice",
      "type": "Person",
      "description": "Alice works at Contoso Corp"
    },
    {
      "name": "Contoso Corp",
      "type": "Organization",
      "description": "Technology company acquired by GlobalTech"
    }
  ],
  "relationships": [
    {
      "source": "Alice",
      "target": "Contoso Corp",
      "relationship": "WorksAt",
      "description": "Alice works at Contoso Corp",
      "strength": 8
    }
  ]
}
"""

def extract_graph_from_text(text):
 
    response = openai.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_4O"),
        messages=[
            {"role": "system", "content": GRAPH_EXTRACTION_PROMPT},
            {"role": "user", "content": text}
        ],
        response_format={"type":"json_object"}
    )

    graph_json = json.loads(response.choices[0].message.content)
    
    return graph_json

def import_to_neo4j(graph_json):
    try:

        with driver.session() as session:
            entities = graph_json.get("entities", [])
            relationships = graph_json.get("relationships", [])

            for entity in entities:
                label = entity["type"]
                name = entity["name"]
                description = entity["description"]

                session.run(
                    f"""
                    MERGE (e:`{label}` {{name: $name}})
                    SET e.description = $description
                    """,
                    {
                        "name":name,
                        "description":description
                    }
                )

            for rel in relationships:
                source = rel["source"]
                target = rel["target"]
                relationship = rel["relationship"]
                description = rel.get("description","")
                
                session.run(
                    f"""
                    MATCH (a {{name: $source}})
                    MATCH (b {{name: $target}})
                    MERGE (a)-[r:`{relationship}`]->(b)
                    SET r.description = $description
                    """,
                    {
                        "source":source,
                        "target":target,
                        "description":description
                    }
                )
        pprint("Data imported to Neo4j successfully.")
    except Exception as e:
        pprint(f"Error importing data to Neo4j: {e}")



if __name__ == "__main__":

    extract_graph_json = ""

    with open("samuel_altman.txt", "r", encoding="utf-8") as file:
        file_content = file.read()
        extracted_graph_json = extract_graph_from_text(file_content)
    
    pprint(extracted_graph_json)

    import_to_neo4j(extracted_graph_json)

