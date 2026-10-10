"""Generate knowledge-graph figures (Graphviz DOT -> PDF/PNG) directly from vietnam-banking.ttl."""
import subprocess, sys, os
import rdflib, rdflib.collection
from rdflib.namespace import RDF, RDFS, OWL
TTL = sys.argv[1]; OUT = sys.argv[2]
g = rdflib.Graph(); g.parse(TTL)
B = "https://data.example.org/vietnam-banking/"; E = rdflib.Namespace(B)
WD, DBR = "http://www.wikidata.org/entity/", "http://dbpedia.org/resource/"
FONT = 'fontname="DejaVu Sans"'
def short(u):
    s = str(u)
    for p, q in [(B+"bank-type/","bt:"),(B+"bank/","bank:"),(B+"location/","loc:"),(B+"service/","sv:"),(B,":"),
                 (WD,"wd:"),(DBR,"dbr:"),("https://schema.org/","schema:"),(str(rdflib.XSD),"xsd:"),(str(RDF),"rdf:"),(str(RDFS),"rdfs:"),(str(OWL),"owl:")]:
        if s.startswith(p): return q + s[len(p):]
    return s
def q(s): return '"' + str(s).replace('"','\\"') + '"'
def render(name, dot):
    p = os.path.join(OUT, name)
    open(p + ".dot", "w").write(dot)
    for fmt in ("pdf", "png"):
        subprocess.run(["dot", f"-T{fmt}", "-Gdpi=200", p + ".dot", "-o", f"{p}.{fmt}"], check=True)

# (a) Schema graph from rdfs:domain / rdfs:range
L = [f'digraph S {{ rankdir=LR; nodesep=0.35; ranksep=0.7; node [{FONT}, fontsize=11]; edge [{FONT}, fontsize=9];']
classes = {E.Bank, E.BankType, E.Location, E.Service}
for c in classes:
    L.append(f'{q(short(c))} [shape=ellipse, style=filled, fillcolor="#FCE9C8"];')
for p in g.subjects(RDF.type, OWL.ObjectProperty):
    d, r = g.value(p, RDFS.domain), g.value(p, RDFS.range)
    if p == E.isHeadquartersOf or p == E.isProvidedBy:  # draw inverses as dashed back-edges
        L.append(f'{q(short(d))} -> {q(short(r))} [label={q(short(p))}, style=dashed, color="#777777", fontcolor="#555555"];')
    else:
        L.append(f'{q(short(d))} -> {q(short(r))} [label={q(short(p))}, color="#1F4E78"];')
for p in g.subjects(RDF.type, OWL.DatatypeProperty):
    r = short(g.value(p, RDFS.range)); n = f"lit_{short(p)}"
    L.append(f'{q(n)} [label={q(r)}, shape=box, style="rounded,filled", fillcolor="#EEEEEE", fontsize=9];')
    L.append(f'":Bank" -> {q(n)} [label={q(short(p))}, color="#888888", fontsize=8];')
defined = [c for c in g.subjects(RDF.type, OWL.Class) if (c, OWL.equivalentClass, None) in g and str(c).startswith(B)]
for c in sorted(defined, key=str):
    L.append(f'{q(short(c))} [shape=ellipse, style="filled,dashed", fillcolor="#E2EFDA"];')
    # label = the restriction read from owl:equivalentClass (owl:intersectionOf Bank + restriction)
    lab = "≡ Bank ⊓ ?"
    for ec in g.objects(c, OWL.equivalentClass):
        for lst in g.objects(ec, OWL.intersectionOf):
            for m in rdflib.collection.Collection(g, lst):
                prop = g.value(m, OWL.onProperty)
                if prop is None: continue
                hv = g.value(m, OWL.hasValue)
                if hv is not None:
                    lab = f"{short(prop)} value {short(hv).split(':',1)[-1]}"
                else:
                    dr = g.value(m, OWL.someValuesFrom)
                    mx = None
                    for wr in g.objects(dr, OWL.withRestrictions):
                        for r in rdflib.collection.Collection(g, wr):
                            mx = g.value(r, rdflib.XSD.maxInclusive)
                    lab = f"{short(prop)} ≤ {mx}" if mx is not None else f"{short(prop)} some ..."
    L.append(f'{q(short(c))} -> ":Bank" [label={q(lab)}, arrowhead=onormal, color="#548235", fontcolor="#548235"];')
L.append('"schema:BankOrCreditUnion" [shape=ellipse, style=filled, fillcolor="#DDEBF7"];')
L.append('":Bank" -> "schema:BankOrCreditUnion" [label="rdfs:subClassOf", arrowhead=onormal, color="#2F5597"];')
L.append("}")
render("kg_schema", "\n".join(L))

# (b) Instance subgraph for two banks, all asserted object links + key literals + sameAs
L = [f'digraph I {{ rankdir=LR; nodesep=0.25; ranksep=0.9; node [{FONT}, fontsize=10]; edge [{FONT}, fontsize=8];']
seen = set()
def node(n, kind):
    if n in seen: return
    seen.add(n)
    style = {"bank":'shape=ellipse, style=filled, fillcolor="#FCE9C8", penwidth=1.5',
             "int":'shape=ellipse, style=filled, fillcolor="#FFF2CC"',
             "ext":'shape=ellipse, style=filled, fillcolor="#DDEBF7"',
             "lit":'shape=box, style="rounded,filled", fillcolor="#EEEEEE", fontsize=9'}[kind]
    L.append(f'{q(n)} [{style}];')
for slug in ["acb", "vietcombank"]:
    b = rdflib.URIRef(B + "bank/" + slug); bn = short(b); node(bn, "bank")
    for p, o in sorted(g.predicate_objects(b), key=lambda x: (str(x[0]), str(x[1]))):
        ps = short(p)
        if p in (E.hasBankType, E.hasHeadquarters, E.operatesInCountry):
            node(short(o), "int"); L.append(f'{q(bn)} -> {q(short(o))} [label={q(ps)}];')
        elif p == E.providesService and str(o).endswith(("digital-banking", "card", "trade-finance")):
            node(short(o), "int"); L.append(f'{q(bn)} -> {q(short(o))} [label={q(ps)}];')
        elif p == OWL.sameAs:
            node(short(o), "ext"); L.append(f'{q(bn)} -> {q(short(o))} [label="owl:sameAs", color="#2F5597", fontcolor="#2F5597", penwidth=1.4];')
        elif p in (E.foundedYear, E.bankId) or (p == RDFS.label and getattr(o, "language", "") == "vi"):
            n = f"{slug}_{ps}"; seen.add(n)
            L.append(f'{q(n)} [label={q(str(o))}, shape=box, style="rounded,filled", fillcolor="#EEEEEE", fontsize=9];')
            L.append(f'{q(bn)} -> {q(n)} [label={q(ps)}, color="#888888"];')
for loc in ["hanoi", "ho-chi-minh-city", "vietnam"]:
    l = rdflib.URIRef(B + "location/" + loc)
    if short(l) in seen:
        for o in g.objects(l, OWL.sameAs):
            node(short(o), "ext"); L.append(f'{q(short(l))} -> {q(short(o))} [label="owl:sameAs", color="#2F5597", fontcolor="#2F5597"];')
L.append("}")
render("kg_instance", "\n".join(L))

# (c) Overview: every bank linked to its type and headquarters (data-driven)
L = [f'digraph O {{ rankdir=LR; nodesep=0.06; ranksep=1.6; splines=true; node [{FONT}, fontsize=9, height=0.22]; edge [arrowsize=0.4, penwidth=0.6];']
types = sorted(set(g.objects(None, E.hasBankType)), key=str)
for t in types:
    lab = g.value(t, RDFS.label, any=False) if False else next((str(x) for x in g.objects(t, RDFS.label) if x.language == "vi"), short(t))
    L.append(f'{q(short(t))} [label={q(lab)}, shape=box, style="rounded,filled", fillcolor="#FCE9C8", fontsize=10];')
banks = sorted([b for b in g.subjects(RDF.type, E.Bank) if str(b).startswith(B + "bank/")], key=lambda b: (str(g.value(b, E.hasBankType)), str(b)))
for b in banks:
    linked = any(str(o).startswith((WD, DBR)) for o in g.objects(b, OWL.sameAs))
    L.append(f'{q(short(b))} [label={q(str(g.value(b, E.abbreviation)))}, shape=ellipse, style=filled, fillcolor={q("#DDEBF7" if linked else "#FFFFFF")}];')
    L.append(f'{q(short(g.value(b, E.hasBankType)))} -> {q(short(b))} [dir=back, color="#BF9000"];')
    L.append(f'{q(short(b))} -> {q(short(g.value(b, E.hasHeadquarters)))} [color="#2F5597"];')
for l in sorted(set(g.objects(None, E.hasHeadquarters)), key=str):
    lab = next(str(x) for x in g.objects(l, RDFS.label) if x.language == "vi")
    L.append(f'{q(short(l))} [label={q(lab)}, shape=box, style="rounded,filled", fillcolor="#FFF2CC", fontsize=10];')
L.append("}")
render("kg_overview", "\n".join(L))
print("ok")
