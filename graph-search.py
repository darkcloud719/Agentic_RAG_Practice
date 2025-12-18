from neo4j import GraphDatabase
from rich import print as pprint

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "P@ssw0rd"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def neo4j_get_graph(tx, cve, hops=1):
    query = """
    WITH $cve AS cve
    UNWIND cve AS en
    MATCH (n)
    WHERE toLower(n.id) = toLower(en)
    MATCH (n)-[r]-(m)
    RETURN n.id AS from, m.name AS to, type(r) AS relationship;
    """

    res = tx.run(query, cve=cve)

    triples_text = []

    for row in res:
        f = row["from"]
        t = row["to"]
        rel = row["relationship"]

        triples_text.append(f"- {f} {rel} {t}")
        
    return {
        "graph_search": triples_text
    }


if __name__ == "__main__":
    with driver.session() as session:
        cve = ["CVE-2025-0010"]
        result = session.execute_read(neo4j_get_graph, cve, hops=1)
        pprint(result)