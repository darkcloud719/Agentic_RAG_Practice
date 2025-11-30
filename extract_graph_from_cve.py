import os, json, openai 
from neo4j import GraphDatabase
from dotenv import load_dotenv
from rich import print as pprint

load_dotenv()

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "P@ssw0rd"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def merge_node(tx, label, key, value):
    query = f"""
    MERGE (n:{label} {{{key}: $value}})
    RETURN n 
    """
    tx.run(query,value=value)

def merge_relation(tx, cve_id, product):
    query = f"""
    MATCH (c:CVE {{id: $cve_id}})
    MATCH (p:Product {{name: $product}})
    MERGE (c)-[:Affect]->(p)
    """
    tx.run(query, cve_id=cve_id, product=product)

def parse_cve_file(path):
    try:
        with open(path,"r",encoding="utf-8") as file:
            data = json.load(file)
        cve_id = data["cveMetadata"]["cveId"]

        products = []
        for a in data["containers"]["cna"].get("affected", []):
            products.append(a.get("product","n/a"))
        return cve_id, products
    except Exception as ex:
        pprint(f"[red]Error pasrsing CVE file {path}: {ex}[/red]")
        return None, None

def process_cve_folder(folder_path):
    # try:
    #     path = os.path.join(os.path.dirname(__file__), "2025", "CVE-2025-0001.json")
    #     with open(path,"r",encoding="utf-8") as file:
    #         data = json.load(file)

    #     cve_id = data["cveMetadata"]["cveId"]

    #     products = []
    #     for a in data["containers"]["cna"].get("affected", []):
    #         products.append(a.get("product","n/a"))

    #     return cve_id, products
    # except Exception as ex:
    #     pprint(f"Error reading CVE JSON file: {ex}")

    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

    pprint(f"[cyan]Found {len(json_files)} CVE JSON files in {folder_path}[/cyan]")

    for file_name in json_files:
        file_path = os.path.join(folder_path, file_name)
        pprint(f"[yellow]Processing {file_name} ...[/yellow]")

        cve_id, products = parse_cve_file(file_path)

        if cve_id and products:
            insert_into_neo4j(cve_id, products)
            pprint(f"[green]Inserted CVE {cve_id} and its products into Neo4j.[/green]")
    
def insert_into_neo4j(cve_id, products):
    try:

        with driver.session() as session:
             
            session.execute_write(merge_node, "CVE", "id", cve_id)

            for product in products:
                session.execute_write(merge_node, "Product", "name", product)
                session.execute_write(merge_relation, cve_id, product)

    except Exception as ex:
        pprint(f"Error reading CVE JSON file: {ex}")

if __name__ == "__main__":
    
    folder = os.path.join(os.path.dirname(__file__), "2025")
    process_cve_folder(folder)
    pprint("[bold green]All CVE files imported to Neo4j![/bold green]")