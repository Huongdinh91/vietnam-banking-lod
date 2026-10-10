"""Load the dataset, run OWL RL reasoning, run the data quality checks and two sample queries.

Usage:  python scripts/validate_and_query.py
Needs:  pip install rdflib owlrl
"""
import time
from pathlib import Path

import owlrl
from rdflib import Graph

DATA = Path(__file__).resolve().parent.parent / "data" / "vietnam-banking.ttl"
NS = "https://data.example.org/vietnam-banking/"
PREFIX = f"""
PREFIX :     <{NS}>
PREFIX loc:  <{NS}location/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
"""
INTERNAL = f'FILTER(STRSTARTS(STR(?bank), "{NS}bank/"))'


def dots(label, width=30):
    return label + " " + "." * max(3, width - len(label)) + " "


def count(g, body):
    return len(list(g.query(PREFIX + body)))


t = time.perf_counter()
g_raw = Graph().parse(DATA, format="turtle")
print(f"[LOAD] {DATA.name} ... {len(g_raw):,} asserted triples "
      f"({(time.perf_counter() - t) * 1000:.0f} ms)")

t = time.perf_counter()
g = Graph()
for triple in g_raw:
    g.add(triple)
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
print(f"[REASON] OWL RL closure ... {len(g):,} triples ({time.perf_counter() - t:.2f} s)")

checks = {
    "bank without type": f"SELECT ?bank WHERE {{ ?bank a :Bank . {INTERNAL} "
                         "FILTER NOT EXISTS { ?bank :hasBankType ?t } }",
    "bank without headquarters": f"SELECT ?bank WHERE {{ ?bank a :Bank . {INTERNAL} "
                                 "FILTER NOT EXISTS { ?bank :hasHeadquarters ?h } }",
    "multiple types / HQs": f"SELECT ?bank WHERE {{ ?bank a :Bank . {INTERNAL} "
                            "{ ?bank :hasBankType ?a, ?b FILTER(?a != ?b) } UNION "
                            "{ ?bank :hasHeadquarters ?a, ?b FILTER(?a != ?b) } }",
    "missing labels": f"SELECT ?bank WHERE {{ ?bank a :Bank . {INTERNAL} "
                      "FILTER NOT EXISTS { ?bank rdfs:label ?l } }",
    "unused location": f'SELECT ?loc WHERE {{ ?loc a :Location . '
                       f'FILTER(STRSTARTS(STR(?loc), "{NS}location/")) '
                       "FILTER NOT EXISTS { ?b :hasHeadquarters ?loc } "
                       "FILTER NOT EXISTS { ?b :operatesInCountry ?loc } }",
}
for label, q in checks.items():
    graph = g if label == "unused location" else g_raw
    print(f"[QUALITY] {dots(label, 26)}{count(graph, q)} violations")
print(f"[QUALITY] {dots('owl:Nothing members', 26)}"
      f"{count(g, 'SELECT ?x WHERE { ?x a owl:Nothing }')} violations")

q3 = f"SELECT DISTINCT ?bank WHERE {{ ?bank :hasHeadquarters loc:hanoi . {INTERNAL} }}"
q9 = f"SELECT ?type (COUNT(DISTINCT ?bank) AS ?n) WHERE {{ ?bank :hasBankType ?type . {INTERNAL} }} GROUP BY ?type"
print(f"[Q3] {dots('Hanoi headquarters', 28)}{count(g, q3)} rows")
print(f"[Q9] {dots('bank type groups', 28)}{count(g, q9)} rows")
print("[DONE] All checks and queries completed.")
