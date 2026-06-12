# SPDX-License-Identifier: Apache-2.0
"""
score_h1_v2.py - H1 edge scoring against the real CGMES model, implementing the
PROPOSAL.md §3.2 frozen taxonomy CORRECTLY (fixes the v1 artifact where every
edge was Type A purely due to relation-label string mismatch).

Pipeline:
  1. Candidate-set entity alignment (exact normalized name; unique fuzzy ≤2;
     duplicate CGMES names produce a candidate SET - charitable to G_LLM).
  2. Relation-label canonicalization via a frozen synonym map
     (natural-language labels → canonical relation classes).
  3. Edge classification:
       MATCH  - endpoint pair supported by a derived CGMES support relation
                (label fidelity reported separately, NOT counted as error)
       TYPE_B - unsupported but expressed in the corpus (sentence co-occurrence
                with relational context) - excluded from precision denominator
       TYPE_A - unsupported, not corpus-expressed, label maps to a schema-class
                relation (asserts structure the schema does not contain)
       TYPE_C - unsupported, not corpus-expressed, unmappable label (no warrant)
  4. Topological recall: fraction of CGMES support pairs (over entities G_LLM
     knows) recovered by any G_LLM edge.

Outputs: data/networks/microgrid/h1_results.json (+ per-edge audit trail h1_edge_audit.json)

Usage: python3 -m src.scoring.h1_edge_classifier
"""

import json
import pathlib
import re
from collections import defaultdict

import os
BASE = pathlib.Path(__file__).resolve().parent.parent.parent
DATA = pathlib.Path(os.environ.get("V2_DATA", BASE / "data" / "networks" / "microgrid"))

# ---------------------------------------------------------------------------
# Load inputs
# ---------------------------------------------------------------------------
std_nodes = json.loads((DATA / "g_std_nodes.json").read_text())
support = json.loads((DATA / "g_std_support.json").read_text())
llm_edges = json.loads((DATA / "g_llm_edges.json").read_text())
llm_entities = json.loads((DATA / "g_llm_entities.json").read_text())
corpus = (DATA / "corpus.txt").read_text()

node_by_id = {n["id"]: n for n in std_nodes}

# ---------------------------------------------------------------------------
# 1. Alignment (frozen): exact normalized name -> candidate set;
#    fallback unique fuzzy <=2; ambiguous fuzzy -> unaligned
# ---------------------------------------------------------------------------
def norm(s):
    s = s.strip().strip('"').lower()
    s = re.sub(r"\s+", " ", s)
    return s

name_index = defaultdict(list)   # normalized name -> [std node ids]
for n in std_nodes:
    if n["name"]:
        name_index[norm(n["name"])].append(n["id"])

def levenshtein(a, b):
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]

# strip class-qualifier prefixes LightRAG tends to attach
PREFIXES = re.compile(
    r"^(busbar section|busbar|ac line segment|line segment|power transformer|"
    r"transformer|synchronous machine|machine|energy consumer|generating unit|"
    r"topological node|substation|voltage level|breaker|shunt compensator|"
    r"linear shunt compensator|(ratio |phase )?tap changer named|"
    r"winding \d+ of( transformer| power transformer)?)\s+",
    re.IGNORECASE)
SUFFIXES = re.compile(
    r"\s+(winding \d+|tap changer|ratio tap changer|windings?)$", re.IGNORECASE)

align_cache = {}
align_report = {"exact": 0, "prefix_stripped": 0, "fuzzy": 0, "ambiguous": 0, "no_match": 0}

def align(llm_name):
    if llm_name in align_cache:
        return align_cache[llm_name]
    q = norm(llm_name)
    result = None
    method = None
    if q in name_index:
        result, method = name_index[q], "exact"
    else:
        q2 = norm(SUFFIXES.sub("", PREFIXES.sub("", llm_name.strip().strip('"'))))
        if q2 in name_index:
            result, method = name_index[q2], "prefix_stripped"
        else:
            # fuzzy <=2 over distinct names
            hits = {}
            for cand_name, ids in name_index.items():
                d = levenshtein(q2, cand_name)
                if d <= 2:
                    hits[cand_name] = ids
            if len(hits) == 1:
                result, method = next(iter(hits.values())), "fuzzy"
            elif len(hits) > 1:
                result, method = None, "ambiguous"
            else:
                result, method = None, "no_match"
    align_report[method] += 1
    align_cache[llm_name] = result
    return result

# ---------------------------------------------------------------------------
# 2. Relation-label canonicalization (frozen synonym map)
# ---------------------------------------------------------------------------
LABEL_MAP = [
    # (regex over label text, canonical class)
    (r"connect|link|interconnect|adjacent|joins|tie|attached|topolog|terminal|node", "CONNECTIVITY"),
    (r"contain|located|installed|within|inside|part of|belongs|member|housed|situated|operates in|region|substation", "CONTAINMENT"),
    (r"has |equipped|component|winding|tap changer|comprises|includes|consists", "PART"),
    (r"voltage|kv |rated|operates at|nominal", "VOLTAGE"),
    (r"feeds|supplies|inject|draw|generat|consum|power flow|delivers", "POWERFLOW"),
]

def canonical_label(rel_text):
    """Multi-keyword labels (LightRAG emits comma-separated keywords) map to a
    SET of canonical classes; empty set = unmappable."""
    t = (rel_text or "").lower()
    classes = set()
    for pat, cls in LABEL_MAP:
        if re.search(pat, t):
            classes.add(cls)
    return classes

# Which canonical label classes are compatible with which support relation
COMPAT = {
    "CONNECTS_TO_NODE": {"CONNECTIVITY", "POWERFLOW"},
    "ELECTRICALLY_CONNECTED": {"CONNECTIVITY", "POWERFLOW"},
    "CONTAINED_IN": {"CONTAINMENT"},
    "HAS_PART": {"PART", "CONTAINMENT"},
    "AT_VOLTAGE": {"VOLTAGE"},
}

# support lookup: pair of std ids (unordered) -> set of support rels
sup_pairs = defaultdict(set)
for s in support:
    sup_pairs[frozenset((s["a"], s["b"]))].add(s["rel"])

# ---------------------------------------------------------------------------
# 3. Corpus-expression check (Type B): both names co-occur in one corpus sentence
# ---------------------------------------------------------------------------
corpus_sentences = [norm(l) for l in corpus.splitlines() if l.strip()]

def corpus_expressed(name_a, name_b):
    a, b = norm(name_a), norm(name_b)
    a = norm(PREFIXES.sub("", name_a))
    b = norm(PREFIXES.sub("", name_b))
    for sent in corpus_sentences:
        if a in sent and b in sent:
            return True
    return False

# ---------------------------------------------------------------------------
# 4. Classify every G_LLM edge
# ---------------------------------------------------------------------------
audit = []
counts = {"MATCH": 0, "TYPE_A": 0, "TYPE_B": 0, "TYPE_C": 0, "UNALIGNED": 0}
label_match = 0

for e in llm_edges:
    A = align(e["src"])
    B = align(e["dst"])
    rec = {"src": e["src"], "dst": e["dst"], "rel": e["rel"]}
    if not A or not B:
        counts["UNALIGNED"] += 1
        rec["class"] = "UNALIGNED"
        audit.append(rec)
        continue
    cls = canonical_label(e["rel"]) | canonical_label(e.get("description", ""))
    rec["canonical_label"] = sorted(cls)
    # support check over candidate sets
    sup = set()
    for a in A:
        for b in B:
            sup |= sup_pairs.get(frozenset((a, b)), set())
    if sup:
        counts["MATCH"] += 1
        rec["class"] = "MATCH"
        rec["support"] = sorted(sup)
        compatible = any(c in COMPAT[s] for s in sup for c in cls)
        rec["label_compatible"] = compatible
        if compatible:
            label_match += 1
    elif corpus_expressed(e["src"], e["dst"]):
        counts["TYPE_B"] += 1
        rec["class"] = "TYPE_B"
    elif cls:
        counts["TYPE_A"] += 1
        rec["class"] = "TYPE_A"
    else:
        counts["TYPE_C"] += 1
        rec["class"] = "TYPE_C"
    audit.append(rec)

aligned_scored = counts["MATCH"] + counts["TYPE_A"] + counts["TYPE_C"]  # B excluded (frozen)
h1_error = (counts["TYPE_A"] + counts["TYPE_C"]) / aligned_scored if aligned_scored else None
label_fidelity = label_match / counts["MATCH"] if counts["MATCH"] else None

# ---------------------------------------------------------------------------
# 5. Topological recall over the aligned entity universe
# ---------------------------------------------------------------------------
# std id -> is it reachable by any aligned LLM entity?
std_covered = set()
for ent in llm_entities:
    ids = align(ent["id"])
    if ids:
        std_covered.update(ids)

# name-level LLM edge pair index
llm_pairs = set()
for e in llm_edges:
    A, B = align(e["src"]), align(e["dst"])
    if A and B:
        for a in A:
            for b in B:
                llm_pairs.add(frozenset((a, b)))

recall_universe = [p for p, rels in sup_pairs.items()
                   if len(p) == 2 and all(x in std_covered for x in p)
                   and rels & {"ELECTRICALLY_CONNECTED", "CONNECTS_TO_NODE", "CONTAINED_IN", "HAS_PART"}]
recovered = sum(1 for p in recall_universe if p in llm_pairs)
topo_recall = recovered / len(recall_universe) if recall_universe else None

# entity coverage
n_aligned_entities = sum(1 for ent in llm_entities if align(ent["id"]))

results = {
    "total_llm_edges": len(llm_edges),
    "total_llm_entities": len(llm_entities),
    "aligned_entities": n_aligned_entities,
    "entity_alignment_rate": round(n_aligned_entities / len(llm_entities), 4) if llm_entities else None,
    "edge_classes": counts,
    "h1_denominator_aligned_scored": aligned_scored,
    "h1_error_rate": round(h1_error, 4) if h1_error is not None else None,
    "h1_match_rate": round(counts["MATCH"] / aligned_scored, 4) if aligned_scored else None,
    "label_fidelity_among_matches": round(label_fidelity, 4) if label_fidelity is not None else None,
    "topological_recall": round(topo_recall, 4) if topo_recall is not None else None,
    "recall_universe_pairs": len(recall_universe),
    "recall_recovered_pairs": recovered,
    "alignment_report": align_report,
    "notes": "MATCH requires CGMES support for the endpoint pair; label mismatch alone is "
             "NOT an error (reported as label_fidelity). TYPE_B excluded from denominator "
             "per frozen protocol.",
}

(DATA / "h1_results.json").write_text(json.dumps(results, indent=2))
(DATA / "h1_edge_audit.json").write_text(json.dumps(audit, indent=2))

print(json.dumps(results, indent=2))
