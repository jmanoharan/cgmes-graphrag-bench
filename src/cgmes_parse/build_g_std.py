# SPDX-License-Identifier: Apache-2.0
"""
build_g_std_cgmes.py - Build G_STD from a REAL CGMES v2.4.15 export
(ENTSO-E MicroGrid Test Configuration, BaseCase Assembled BE+NL+Boundary).

This replaces the v1 pandapower-based builder. Differences (fixes review findings):
  * Ground truth is a genuine IEC 61970/CGMES export with real mRIDs and real
    CIM association names (Terminal.ConductingEquipment, Equipment.EquipmentContainer, ...)
    - NOT invented relation labels.
  * Corpus is a DETERMINISTIC natural-language rendering of the model (no LLM),
    removing same-model circularity from corpus generation.
  * Every corpus relational sentence is logged to corpus_facts.json BEFORE G_LLM
    is built (frozen Type-B "corpus-expressible" registry per PROPOSAL.md §3.2).
  * QA gold answers carry machine-checkable answer_spec for deterministic scoring.

Inputs:  data/cgmes/MicroGrid_BC_Assembled/*.xml  (EQ/TP/SSH BE+NL, EQ/TP BD, SV)
Outputs: data/networks/microgrid/g_std_nodes.json      - CIM objects (mRID, class, name, attrs)
         data/networks/microgrid/g_std_edges.json      - real CIM association edges
         data/networks/microgrid/g_std_support.json    - derived semantic support relations (frozen rules)
         data/networks/microgrid/corpus.txt            - deterministic corpus
         data/networks/microgrid/corpus_facts.json     - corpus-expressible fact registry (Type B oracle)
         data/networks/microgrid/cim_qa_items.json     - 50 QA items, S1/S2, answer_spec
         data/networks/microgrid/h3_g_std_cost.json    - G_STD build cost log

Usage: python3 -m src.cgmes_parse.build_g_std
"""

import argparse
import json
import pathlib
import time
import xml.etree.ElementTree as ET
from collections import defaultdict

import os
BASE = pathlib.Path(__file__).resolve().parent.parent.parent
ENV = BASE / ".env"  # Optional local key file; runtime falls back to environment variables.
_parser = argparse.ArgumentParser(add_help=True)
_parser.add_argument("--case", choices=["microgrid", "smallgrid"], default="microgrid")
_args, _unknown = _parser.parse_known_args()
_default_cgmes = "SmallGrid_BC" if _args.case == "smallgrid" else "MicroGrid_BC_Assembled"
_default_data = "smallgrid" if _args.case == "smallgrid" else "microgrid"
CGMES_DIR = pathlib.Path(os.environ.get("CGMES_DIR", BASE / "data" / "cgmes" / _default_cgmes))
OUT = pathlib.Path(os.environ.get("V2_DATA", BASE / "data" / "networks" / _default_data))
OUT.mkdir(parents=True, exist_ok=True)

RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"

# CIM classes kept in G_STD (core equipment + topology; limits/curves/controls
# are out of scope for the QA study: documented in DEVIATIONS.md)
KEEP_CLASSES = {
    "GeographicalRegion", "SubGeographicalRegion", "Substation", "VoltageLevel",
    "BaseVoltage", "Line", "ACLineSegment", "BusbarSection", "PowerTransformer",
    "PowerTransformerEnd", "RatioTapChanger", "PhaseTapChangerAsymmetrical",
    "SynchronousMachine", "GeneratingUnit", "EnergyConsumer",
    "LinearShuntCompensator", "EquivalentInjection", "Breaker", "Junction",
    "Terminal", "ConnectivityNode", "TopologicalNode",
}

# CIM association properties kept as G_STD edges (REAL schema relations)
KEEP_REFS = {
    "Terminal.ConductingEquipment", "Terminal.TopologicalNode", "Terminal.ConnectivityNode",
    "ConnectivityNode.TopologicalNode", "ConnectivityNode.ConnectivityNodeContainer",
    "Equipment.EquipmentContainer", "VoltageLevel.Substation", "VoltageLevel.BaseVoltage",
    "ConductingEquipment.BaseVoltage", "TopologicalNode.BaseVoltage",
    "TopologicalNode.ConnectivityNodeContainer", "PowerTransformerEnd.PowerTransformer",
    "TransformerEnd.Terminal", "TransformerEnd.BaseVoltage",
    "RotatingMachine.GeneratingUnit", "RatioTapChanger.TransformerEnd",
    "PhaseTapChanger.TransformerEnd", "Substation.Region", "SubGeographicalRegion.Region",
}

# Numeric / literal attributes kept on nodes
KEEP_ATTRS = {
    "IdentifiedObject.name", "IdentifiedObject.description",
    "BaseVoltage.nominalVoltage",
    "ACLineSegment.r", "ACLineSegment.x", "Conductor.length",
    "PowerTransformerEnd.ratedU", "PowerTransformerEnd.ratedS",
    "TransformerEnd.endNumber",
    "GeneratingUnit.maxOperatingP", "GeneratingUnit.minOperatingP",
    "GeneratingUnit.initialP", "GeneratingUnit.nominalP",
    "SynchronousMachine.ratedS",
    "EnergyConsumer.p", "EnergyConsumer.q",                      # SSH
    "RotatingMachine.p", "RotatingMachine.q",                    # SSH
    "EquivalentInjection.p", "EquivalentInjection.q",            # SSH
    "ShuntCompensator.sections",                                 # SSH
    "LinearShuntCompensator.bPerSection", "ShuntCompensator.nomU",
    "TapChanger.step", "TapChanger.neutralStep", "TapChanger.lowStep",
    "TapChanger.highStep", "RatioTapChanger.stepVoltageIncrement",
    "Switch.open",                                               # SSH
}

t0 = time.time()

# ---------------------------------------------------------------------------
# 1. Parse all profile files into a single object registry
# ---------------------------------------------------------------------------
objects = {}   # id -> {"class": str, "attrs": {}, "refs": {prop: [target_id,...]}}

def localname(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag

def norm_id(raw):
    raw = raw.strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if raw.startswith("urn:uuid:"):
        raw = "_" + raw[len("urn:uuid:"):]
    return raw

files = sorted(CGMES_DIR.glob("*.xml"))
assert files, f"No CGMES XML files found in {CGMES_DIR}"

for f in files:
    root = ET.parse(f).getroot()
    for el in root:
        cls = localname(el.tag)
        if cls == "FullModel":
            continue
        oid = el.get(f"{RDF}ID") or el.get(f"{RDF}about")
        if oid is None:
            continue
        oid = norm_id(oid)
        obj = objects.setdefault(oid, {"class": None, "attrs": {}, "refs": defaultdict(list)})
        # rdf:ID elements define the class; rdf:about elements (TP/SSH) augment
        if el.get(f"{RDF}ID") is not None or obj["class"] is None:
            # don't let SSH/TP 'Terminal' rdf:about override an EQ class
            if obj["class"] is None:
                obj["class"] = cls
        for child in el:
            prop = localname(child.tag)
            res = child.get(f"{RDF}resource")
            if res is not None:
                if res.startswith("#") or res.startswith("urn:uuid:"):
                    obj["refs"][prop].append(norm_id(res))
            else:
                if child.text is not None:
                    obj["attrs"][prop] = child.text.strip()

print(f"Parsed {len(files)} files, {len(objects)} CIM objects")

# ---------------------------------------------------------------------------
# 2. Build G_STD nodes + edges (kept classes / kept associations only)
# ---------------------------------------------------------------------------
kept_ids = {oid for oid, o in objects.items() if o["class"] in KEEP_CLASSES}

def attrs_of(oid):
    o = objects[oid]
    out = {}
    for k, v in o["attrs"].items():
        if k in KEEP_ATTRS:
            short = k.split(".", 1)[1]
            try:
                out[short] = float(v)
            except ValueError:
                out[short] = v
    return out

nodes = []
for oid in sorted(kept_ids):
    o = objects[oid]
    nodes.append({
        "mrid": oid.lstrip("_"),
        "id": oid,
        "class": o["class"],
        "name": o["attrs"].get("IdentifiedObject.name", ""),
        "attrs": attrs_of(oid),
    })

edges = []
for oid in sorted(kept_ids):
    o = objects[oid]
    for prop, targets in o["refs"].items():
        if prop not in KEEP_REFS:
            continue
        for t in targets:
            if t in kept_ids:
                edges.append({"src": oid, "rel": prop, "dst": t})

node_by_id = {n["id"]: n for n in nodes}
print(f"G_STD: {len(nodes)} nodes, {len(edges)} edges "
      f"({len(set(e['rel'] for e in edges))} distinct CIM association types)")

# ---------------------------------------------------------------------------
# 3. Derived semantic support relations (frozen rules, deterministic)
#    These are what natural language can plausibly express; each is derived
#    from explicit CIM associations by a fixed rule.
# ---------------------------------------------------------------------------
ref1 = lambda oid, prop: (objects[oid]["refs"].get(prop) or [None])[0]

terminals = [oid for oid in kept_ids if objects[oid]["class"] == "Terminal"]
eq_tns = defaultdict(set)     # equipment id -> set of TopologicalNode ids
tn_eqs = defaultdict(set)
for t in terminals:
    eq = ref1(t, "Terminal.ConductingEquipment")
    tn = ref1(t, "Terminal.TopologicalNode")
    if tn is None:
        cn = ref1(t, "Terminal.ConnectivityNode")
        if cn:
            tn = ref1(cn, "ConnectivityNode.TopologicalNode")
    if eq in kept_ids and tn in kept_ids:
        eq_tns[eq].add(tn)
        tn_eqs[tn].add(eq)

support = []  # list of {a, rel, b} canonical support relations

# CONNECTS_TO_NODE: equipment <-> topological node (via Terminal)
for eq, tns in eq_tns.items():
    for tn in tns:
        support.append({"a": eq, "rel": "CONNECTS_TO_NODE", "b": tn})

# ELECTRICALLY_CONNECTED: equipment pair sharing >=1 TopologicalNode
for tn, eqs in tn_eqs.items():
    eqs = sorted(eqs)
    for i in range(len(eqs)):
        for j in range(i + 1, len(eqs)):
            support.append({"a": eqs[i], "rel": "ELECTRICALLY_CONNECTED", "b": eqs[j]})

# CONTAINED_IN: equipment -> container (direct) and -> substation (transitive)
def container_chain(oid):
    chain = []
    c = ref1(oid, "Equipment.EquipmentContainer")
    while c and c in kept_ids:
        chain.append(c)
        nxt = None
        if objects[c]["class"] == "VoltageLevel":
            nxt = ref1(c, "VoltageLevel.Substation")
        chain_next = nxt
        c = chain_next
    return chain

for oid in sorted(kept_ids):
    if objects[oid]["class"] in ("ACLineSegment", "BusbarSection", "PowerTransformer",
                                 "SynchronousMachine", "EnergyConsumer",
                                 "LinearShuntCompensator", "Breaker", "EquivalentInjection"):
        for c in container_chain(oid):
            support.append({"a": oid, "rel": "CONTAINED_IN", "b": c})

# VoltageLevel -> Substation, Substation -> Region
for oid in sorted(kept_ids):
    cls = objects[oid]["class"]
    if cls == "VoltageLevel":
        s = ref1(oid, "VoltageLevel.Substation")
        if s in kept_ids:
            support.append({"a": oid, "rel": "CONTAINED_IN", "b": s})
    if cls == "Substation":
        r = ref1(oid, "Substation.Region")
        if r in kept_ids:
            support.append({"a": oid, "rel": "CONTAINED_IN", "b": r})
            gr = ref1(r, "SubGeographicalRegion.Region")
            if gr in kept_ids:
                support.append({"a": oid, "rel": "CONTAINED_IN", "b": gr})
    if cls == "TopologicalNode":
        cont = ref1(oid, "TopologicalNode.ConnectivityNodeContainer")
        if cont in kept_ids:
            support.append({"a": oid, "rel": "CONTAINED_IN", "b": cont})
            if objects[cont]["class"] == "VoltageLevel":
                s = ref1(cont, "VoltageLevel.Substation")
                if s in kept_ids:
                    support.append({"a": oid, "rel": "CONTAINED_IN", "b": s})

# HAS_PART: transformer -> ends -> tap changers; generating unit -> machine
for oid in sorted(kept_ids):
    cls = objects[oid]["class"]
    if cls == "PowerTransformerEnd":
        tr = ref1(oid, "PowerTransformerEnd.PowerTransformer")
        if tr in kept_ids:
            support.append({"a": tr, "rel": "HAS_PART", "b": oid})
    if cls in ("RatioTapChanger", "PhaseTapChangerAsymmetrical"):
        end = ref1(oid, "RatioTapChanger.TransformerEnd") or ref1(oid, "PhaseTapChanger.TransformerEnd")
        if end in kept_ids:
            support.append({"a": end, "rel": "HAS_PART", "b": oid})
            tr = ref1(end, "PowerTransformerEnd.PowerTransformer")
            if tr in kept_ids:
                support.append({"a": tr, "rel": "HAS_PART", "b": oid})
    if cls == "SynchronousMachine":
        gu = ref1(oid, "RotatingMachine.GeneratingUnit")
        if gu in kept_ids:
            support.append({"a": gu, "rel": "HAS_PART", "b": oid})

# AT_VOLTAGE: object -> BaseVoltage
for oid in sorted(kept_ids):
    o = objects[oid]
    for prop in ("ConductingEquipment.BaseVoltage", "VoltageLevel.BaseVoltage",
                 "TopologicalNode.BaseVoltage", "TransformerEnd.BaseVoltage"):
        bv = ref1(oid, prop)
        if bv in kept_ids:
            support.append({"a": oid, "rel": "AT_VOLTAGE", "b": bv})

# Transitive containment closure into regions: X ⊂ Substation ⊂ Region ⊂ GeoRegion
sub_region = {}
for oid in sorted(kept_ids):
    if objects[oid]["class"] == "Substation":
        r = ref1(oid, "Substation.Region")
        regs = []
        if r in kept_ids:
            regs.append(r)
            gr = ref1(r, "SubGeographicalRegion.Region")
            if gr in kept_ids:
                regs.append(gr)
        sub_region[oid] = regs
extra = []
for s in support:
    if s["rel"] == "CONTAINED_IN" and s["b"] in sub_region:
        for r in sub_region[s["b"]]:
            extra.append({"a": s["a"], "rel": "CONTAINED_IN", "b": r})
support.extend(extra)

# Dedup support
seen = set()
support_dedup = []
for s in support:
    k = (s["a"], s["rel"], s["b"])
    if k not in seen:
        seen.add(k)
        support_dedup.append(s)
support = support_dedup
print(f"Support relations: {len(support)} "
      f"({len(set(s['rel'] for s in support))} canonical types)")

# ---------------------------------------------------------------------------
# 4. Helper views for corpus + QA
# ---------------------------------------------------------------------------
def name(oid, fallback_mrid=True):
    if oid is None:
        return "?"
    n = node_by_id.get(oid, {}).get("name", "")
    if n:
        return n
    return oid.lstrip("_")[:8] if fallback_mrid else ""

def nominal_kv(oid):
    """Nominal voltage of an object via its BaseVoltage association."""
    for prop in ("ConductingEquipment.BaseVoltage", "VoltageLevel.BaseVoltage",
                 "TopologicalNode.BaseVoltage", "TransformerEnd.BaseVoltage"):
        bv = ref1(oid, prop)
        if bv in kept_ids:
            return node_by_id[bv]["attrs"].get("nominalVoltage")
    return None

def of_class(cls):
    return [oid for oid in sorted(kept_ids) if objects[oid]["class"] == cls]

def vl_of(oid):
    c = ref1(oid, "Equipment.EquipmentContainer")
    if c in kept_ids and objects[c]["class"] == "VoltageLevel":
        return c
    return None

def substation_of(oid):
    if objects[oid]["class"] == "VoltageLevel":
        return ref1(oid, "VoltageLevel.Substation")
    c = ref1(oid, "Equipment.EquipmentContainer")
    if c in kept_ids:
        if objects[c]["class"] == "VoltageLevel":
            return ref1(c, "VoltageLevel.Substation")
        if objects[c]["class"] == "Substation":
            return c
    return None

def region_of_substation(sub):
    r = ref1(sub, "Substation.Region")
    if r in kept_ids:
        gr = ref1(r, "SubGeographicalRegion.Region")
        if gr in kept_ids:
            return name(gr)
        return name(r)
    return None

def tns_of_eq(oid):
    return sorted(eq_tns.get(oid, set()), key=lambda x: name(x))

def trafo_ends(tr):
    ends = [oid for oid in of_class("PowerTransformerEnd")
            if ref1(oid, "PowerTransformerEnd.PowerTransformer") == tr]
    return sorted(ends, key=lambda e: node_by_id[e]["attrs"].get("endNumber", 0))

def end_tn(end):
    t = ref1(end, "TransformerEnd.Terminal")
    if t:
        tn = ref1(t, "Terminal.TopologicalNode")
        if tn is None:
            cn = ref1(t, "Terminal.ConnectivityNode")
            if cn:
                tn = ref1(cn, "ConnectivityNode.TopologicalNode")
        return tn
    return None

# name uniqueness check (alignment protocol relies on names)
from collections import Counter
name_counts = Counter(name(oid) for oid in kept_ids if node_by_id[oid]["name"])
dups = {n: c for n, c in name_counts.items() if c > 1}
if dups:
    print(f"WARNING - duplicate names (will be ambiguity-excluded in alignment): {dups}")

# ---------------------------------------------------------------------------
# 5. Deterministic corpus + corpus-fact registry
# ---------------------------------------------------------------------------
corpus_lines = []
facts = []  # {"a": name, "rel": canonical, "b": name, "sentence": str}

def emit(sentence, fact_triples=()):
    corpus_lines.append(sentence)
    for (a, rel, b) in fact_triples:
        facts.append({"a": a, "rel": rel, "b": b, "sentence": sentence})

regions = of_class("GeographicalRegion")
subs = of_class("Substation")
lines_ = of_class("ACLineSegment")
trafos = of_class("PowerTransformer")
machines = of_class("SynchronousMachine")
loads = of_class("EnergyConsumer")
shunts = of_class("LinearShuntCompensator")
busbars = of_class("BusbarSection")
breakers = of_class("Breaker")
tns = of_class("TopologicalNode")

corpus_lines.append("ENTSO-E CGMES MicroGrid Test Configuration - Network Operations Description")
corpus_lines.append("=" * 78)
corpus_lines.append("")
emit(f"This document describes an interconnected transmission network spanning "
     f"{len(regions)} geographical regions ({', '.join(sorted(name(r) for r in regions))}), "
     f"with {len(subs)} substations, {len(lines_)} AC line segments, {len(trafos)} power "
     f"transformers, {len(machines)} synchronous machines, and {len(loads)} energy consumers.")
corpus_lines.append("")

corpus_lines.append("Substations and Voltage Levels")
corpus_lines.append("-" * 40)
for s in subs:
    reg = region_of_substation(s)
    emit(f"Substation {name(s)} is located in the {reg} region.",
         [(name(s), "CONTAINED_IN", reg)])
    vls = [v for v in of_class("VoltageLevel") if ref1(v, "VoltageLevel.Substation") == s]
    for v in sorted(vls, key=lambda x: -(nominal_kv(x) or 0)):
        kv = nominal_kv(v)
        emit(f"Substation {name(s)} contains voltage level {name(v)} with a nominal "
             f"voltage of {kv:g} kV.",
             [(name(v), "CONTAINED_IN", name(s)), (name(v), "AT_VOLTAGE", f"{kv:g} kV")])
corpus_lines.append("")

corpus_lines.append("Busbars and Topological Nodes")
corpus_lines.append("-" * 40)
for b in busbars:
    vl = vl_of(b)
    sub = substation_of(b)
    kv = nominal_kv(b) or (nominal_kv(vl) if vl else None)
    btns = tns_of_eq(b)
    sent = (f"Busbar section {name(b)} is installed in voltage level {name(vl)} "
            f"of substation {name(sub)} and operates at a nominal voltage of {kv:g} kV.")
    fl = [(name(b), "CONTAINED_IN", name(vl)), (name(b), "CONTAINED_IN", name(sub)),
          (name(b), "AT_VOLTAGE", f"{kv:g} kV")]
    if btns:
        sent += f" It corresponds to topological node {name(btns[0])}."
        fl.append((name(b), "CONNECTS_TO_NODE", name(btns[0])))
    emit(sent, fl)
corpus_lines.append("")

corpus_lines.append("AC Transmission Lines")
corpus_lines.append("-" * 40)
for l in lines_:
    a = node_by_id[l]["attrs"]
    ltns = tns_of_eq(l)
    ends = [name(t) for t in ltns]
    kv = nominal_kv(l)
    sent = f"AC line segment {name(l)} "
    if len(ends) == 2:
        sent += f"connects topological node {ends[0]} to topological node {ends[1]}. "
    elif len(ends) == 1:
        sent += f"is connected to topological node {ends[0]} at one end. "
    sent += (f"It has a length of {a.get('length', 0):g} km, a resistance of "
             f"{a.get('r', 0):g} ohm, a reactance of {a.get('x', 0):g} ohm")
    if kv:
        sent += f", and operates at {kv:g} kV"
    sent += "."
    fl = [(name(l), "CONNECTS_TO_NODE", e) for e in ends]
    if len(ends) == 2:
        fl.append((ends[0], "ELECTRICALLY_CONNECTED", ends[1]))
    if kv:
        fl.append((name(l), "AT_VOLTAGE", f"{kv:g} kV"))
    emit(sent, fl)
corpus_lines.append("")

corpus_lines.append("Power Transformers")
corpus_lines.append("-" * 40)
for tr in trafos:
    sub = substation_of(tr)
    ends = trafo_ends(tr)
    n_w = len(ends)
    emit(f"Power transformer {name(tr)} is a {n_w}-winding transformer installed in "
         f"substation {name(sub)}.",
         [(name(tr), "CONTAINED_IN", name(sub))])
    for e in ends:
        ea = node_by_id[e]["attrs"]
        tn = end_tn(e)
        endno = int(ea.get("endNumber", 0))
        sent = (f"Winding {endno} of transformer {name(tr)} has a rated voltage of "
                f"{ea.get('ratedU', 0):g} kV and a rated apparent power of "
                f"{ea.get('ratedS', 0):g} MVA")
        fl = [(name(tr), "HAS_PART", f"winding {endno}")]
        if tn:
            sent += f", and is connected to topological node {name(tn)}"
            fl.append((name(tr), "CONNECTS_TO_NODE", name(tn)))
        sent += "."
        emit(sent, fl)
    # tap changers
    for e in ends:
        for tc in of_class("RatioTapChanger") + of_class("PhaseTapChangerAsymmetrical"):
            tce = ref1(tc, "RatioTapChanger.TransformerEnd") or ref1(tc, "PhaseTapChanger.TransformerEnd")
            if tce == e:
                kind = ("ratio tap changer" if objects[tc]["class"] == "RatioTapChanger"
                        else "asymmetrical phase tap changer")
                ta = node_by_id[tc]["attrs"]
                fmt = lambda v: f"{v:g}" if isinstance(v, float) else "?"
                emit(f"Transformer {name(tr)} is equipped with a {kind} named {name(tc)} "
                     f"on winding {int(node_by_id[e]['attrs'].get('endNumber', 0))}, "
                     f"with steps from {fmt(ta.get('lowStep'))} to {fmt(ta.get('highStep'))} "
                     f"and neutral step {fmt(ta.get('neutralStep'))}.",
                     [(name(tr), "HAS_PART", name(tc))])
corpus_lines.append("")

corpus_lines.append("Generation")
corpus_lines.append("-" * 40)
for m in machines:
    gu = ref1(m, "RotatingMachine.GeneratingUnit")
    vl = vl_of(m)
    sub = substation_of(m)
    mtns = tns_of_eq(m)
    ma = node_by_id[m]["attrs"]
    gua = node_by_id[gu]["attrs"] if gu in kept_ids else {}
    sent = (f"Synchronous machine {name(m)} (rated apparent power "
            f"{ma.get('ratedS', 0):g} MVA) operates in voltage level {name(vl)} of "
            f"substation {name(sub)}.")
    fl = [(name(m), "CONTAINED_IN", name(vl)), (name(m), "CONTAINED_IN", name(sub))]
    if mtns:
        sent += f" It is connected to topological node {name(mtns[0])}."
        fl.append((name(m), "CONNECTS_TO_NODE", name(mtns[0])))
    emit(sent, fl)
    if gu in kept_ids:
        emit(f"Machine {name(m)} belongs to generating unit {name(gu)}, which has a "
             f"maximum operating power of {gua.get('maxOperatingP', 0):g} MW and a "
             f"minimum operating power of {gua.get('minOperatingP', 0):g} MW.",
             [(name(gu), "HAS_PART", name(m))])
    p, q = ma.get("p"), ma.get("q")
    if p is not None:
        emit(f"In the studied operating case, machine {name(m)} injects an active power "
             f"of {-p:g} MW and a reactive power of {-q:g} MVAr into the network.", [])
corpus_lines.append("")

corpus_lines.append("Loads")
corpus_lines.append("-" * 40)
for ld in loads:
    vl = vl_of(ld)
    sub = substation_of(ld)
    la = node_by_id[ld]["attrs"]
    ltns = tns_of_eq(ld)
    sent = (f"Energy consumer {name(ld)} draws an active power of {la.get('p', 0):g} MW "
            f"and a reactive power of {la.get('q', 0):g} MVAr. It is located in voltage "
            f"level {name(vl)} of substation {name(sub)}")
    fl = [(name(ld), "CONTAINED_IN", name(vl)), (name(ld), "CONTAINED_IN", name(sub))]
    if ltns:
        sent += f", connected to topological node {name(ltns[0])}"
        fl.append((name(ld), "CONNECTS_TO_NODE", name(ltns[0])))
    sent += "."
    emit(sent, fl)
corpus_lines.append("")

corpus_lines.append("Reactive Compensation and Switching Devices")
corpus_lines.append("-" * 40)
for sh in shunts:
    vl = vl_of(sh)
    sub = substation_of(sh)
    sa = node_by_id[sh]["attrs"]
    stns = tns_of_eq(sh)
    sent = (f"Linear shunt compensator {name(sh)} is installed in voltage level "
            f"{name(vl)} of substation {name(sub)}")
    fl = [(name(sh), "CONTAINED_IN", name(vl)), (name(sh), "CONTAINED_IN", name(sub))]
    if stns:
        sent += f" at topological node {name(stns[0])}"
        fl.append((name(sh), "CONNECTS_TO_NODE", name(stns[0])))
    sent += (f", with a susceptance per section of {sa.get('bPerSection', 0):g} S and "
             f"{sa.get('sections', 0):g} energized sections in the studied case.")
    emit(sent, fl)
for br in breakers:
    vl = vl_of(br)
    sub = substation_of(br)
    btns = tns_of_eq(br)
    state = "open" if str(node_by_id[br]["attrs"].get("open", "")).lower() == "true" else "closed"
    sent = f"Breaker {name(br)} in voltage level {name(vl)} of substation {name(sub)} is currently {state}."
    fl = [(name(br), "CONTAINED_IN", name(vl)), (name(br), "CONTAINED_IN", name(sub))]
    if len(btns) == 2:
        sent += (f" It connects topological node {name(btns[0])} to topological node "
                 f"{name(btns[1])}.")
        fl += [(name(br), "CONNECTS_TO_NODE", name(btns[0])),
               (name(br), "CONNECTS_TO_NODE", name(btns[1]))]
    emit(sent, fl)
corpus_lines.append("")

corpus_text = "\n".join(corpus_lines)
(OUT / "corpus.txt").write_text(corpus_text)
(OUT / "corpus_facts.json").write_text(json.dumps(facts, indent=2))
print(f"Corpus: {len(corpus_text.split())} words, {len(corpus_text)} chars; "
      f"{len(facts)} registered corpus facts")

# ---------------------------------------------------------------------------
# 6. QA generation: 25 S1 (single-hop) + 25 S2 (multi-hop), deterministic gold
# ---------------------------------------------------------------------------
qa = []

# QA must reference uniquely-named entities only: some CGMES exports reuse a
# name across distinct objects of the SAME class (e.g., SmallGrid has two
# ACLineSegments both named "49-54"), which makes a question ill-posed.
def class_unique(oid):
    nm = name(oid)
    cls = objects[oid]["class"]
    return sum(1 for o in kept_ids
               if objects[o]["class"] == cls and name(o) == nm) == 1

lines_ = [l for l in lines_ if class_unique(l)]
trafos = [t for t in trafos if class_unique(t)]
machines = [m for m in machines if class_unique(m)]
loads = [ld for ld in loads if class_unique(ld)]
busbars = [b for b in busbars if class_unique(b)]
print(f"QA-eligible (unique-named): lines={len(lines_)} trafos={len(trafos)} "
      f"machines={len(machines)} loads={len(loads)} busbars={len(busbars)}")

def add_qa(question, gold, spec, stratum, hops, evidence):
    qa.append({
        "id": f"Q{len(qa)+1:02d}",
        "question": question,
        "gold_answer": gold,
        "answer_spec": spec,
        "stratum": stratum,
        "hop_count": hops,
        "evidence": evidence,
    })

# ---- S1: attribute lookups / single-association lookups (need 25)
s1_cands = []

for l in lines_:
    a = node_by_id[l]["attrs"]
    s1_cands.append((
        f"What is the length (in km) of AC line segment {name(l)}?",
        f"{a.get('length', 0):g} km",
        {"type": "number", "value": a.get("length", 0), "unit": "km", "tol": 0.01},
        f"{name(l)}.Conductor.length"))
    s1_cands.append((
        f"What is the positive-sequence resistance (in ohm) of AC line segment {name(l)}?",
        f"{a.get('r', 0):g} ohm",
        {"type": "number", "value": a.get("r", 0), "unit": "ohm", "tol": 0.01},
        f"{name(l)}.ACLineSegment.r"))

for tr in trafos:
    for e in trafo_ends(tr):
        ea = node_by_id[e]["attrs"]
        endno = int(ea.get("endNumber", 0))
        s1_cands.append((
            f"What is the rated voltage (in kV) of winding {endno} of power transformer {name(tr)}?",
            f"{ea.get('ratedU', 0):g} kV",
            {"type": "number", "value": ea.get("ratedU", 0), "unit": "kV", "tol": 0.01},
            f"{name(tr)}.end{endno}.ratedU"))

for m in machines:
    gu = ref1(m, "RotatingMachine.GeneratingUnit")
    if gu in kept_ids:
        gua = node_by_id[gu]["attrs"]
        s1_cands.append((
            f"What is the maximum operating power (in MW) of generating unit {name(gu)}?",
            f"{gua.get('maxOperatingP', 0):g} MW",
            {"type": "number", "value": gua.get("maxOperatingP", 0), "unit": "MW", "tol": 0.01},
            f"{name(gu)}.maxOperatingP"))

for ld in loads:
    la = node_by_id[ld]["attrs"]
    s1_cands.append((
        f"What is the active power (in MW) drawn by energy consumer {name(ld)}?",
        f"{la.get('p', 0):g} MW",
        {"type": "number", "value": la.get("p", 0), "unit": "MW", "tol": 0.01},
        f"{name(ld)}.EnergyConsumer.p"))

# NOTE: VoltageLevel-name QA dropped: CGMES MicroGrid names voltage levels
# numerically ("220.0"), which both leaks the answer and is ambiguous across
# substations. Replaced with additional attribute families below.
for l in lines_:
    a = node_by_id[l]["attrs"]
    s1_cands.append((
        f"What is the positive-sequence reactance (in ohm) of AC line segment {name(l)}?",
        f"{a.get('x', 0):g} ohm",
        {"type": "number", "value": a.get("x", 0), "unit": "ohm", "tol": 0.01},
        f"{name(l)}.ACLineSegment.x"))

for tr in trafos:
    for e in trafo_ends(tr):
        ea = node_by_id[e]["attrs"]
        endno = int(ea.get("endNumber", 0))
        s1_cands.append((
            f"What is the rated apparent power (in MVA) of winding {endno} of power transformer {name(tr)}?",
            f"{ea.get('ratedS', 0):g} MVA",
            {"type": "number", "value": ea.get("ratedS", 0), "unit": "MVA", "tol": 0.01},
            f"{name(tr)}.end{endno}.ratedS"))

for ld in loads:
    la = node_by_id[ld]["attrs"]
    s1_cands.append((
        f"What is the reactive power (in MVAr) drawn by energy consumer {name(ld)}?",
        f"{la.get('q', 0):g} MVAr",
        {"type": "number", "value": la.get("q", 0), "unit": "MVAr", "tol": 0.01},
        f"{name(ld)}.EnergyConsumer.q"))

for m in machines:
    gu = ref1(m, "RotatingMachine.GeneratingUnit")
    if gu in kept_ids:
        gua = node_by_id[gu]["attrs"]
        s1_cands.append((
            f"What is the minimum operating power (in MW) of generating unit {name(gu)}?",
            f"{gua.get('minOperatingP', 0):g} MW",
            {"type": "number", "value": gua.get("minOperatingP", 0), "unit": "MW", "tol": 0.01},
            f"{name(gu)}.minOperatingP"))

# interleave candidate families for diversity, take 25
import itertools
def interleave(seq, step):
    return [seq[i] for i in range(0, len(seq), step)]
s1_sel = []
used_q = set()
for cand in itertools.chain(interleave(s1_cands, 3), s1_cands):
    if len(s1_sel) >= 25:
        break
    if cand[0] in used_q:
        continue
    used_q.add(cand[0])
    s1_sel.append(cand)
for (q, g, spec, ev) in s1_sel:
    add_qa(q, g, spec, "S1", 1, ev)

# ---- S2: multi-hop (need 25)
s2_cands = []

# busbar -> VL -> substation (2 hops)
for b in busbars:
    sub = substation_of(b)
    if sub:
        s2_cands.append((
            f"Which substation contains busbar section {name(b)}?",
            f"{name(sub)}",
            {"type": "entity", "value": name(sub)},
            2, f"{name(b)}->VL->Substation"))

# line -> 2 TNs (via terminals, 2 hops)
for l in lines_:
    ends = [name(t) for t in tns_of_eq(l)]
    if len(ends) == 2:
        s2_cands.append((
            f"Which two topological nodes does AC line segment {name(l)} connect?",
            f"{ends[0]} and {ends[1]}",
            {"type": "entity_set", "values": ends},
            2, f"{name(l)}->Terminals->TNs"))

# machine -> generating unit -> maxP (2 hops)
for m in machines:
    gu = ref1(m, "RotatingMachine.GeneratingUnit")
    if gu in kept_ids:
        gua = node_by_id[gu]["attrs"]
        s2_cands.append((
            f"What is the maximum operating power (in MW) of the generating unit that "
            f"synchronous machine {name(m)} belongs to?",
            f"{gua.get('maxOperatingP', 0):g} MW",
            {"type": "number", "value": gua.get("maxOperatingP", 0), "unit": "MW", "tol": 0.01},
            2, f"{name(m)}->GU->maxP"))

# transformer -> winding 1 -> TN (2 hops)
for tr in trafos:
    ends = trafo_ends(tr)
    if ends:
        tn = end_tn(ends[0])
        if tn:
            s2_cands.append((
                f"Which topological node is winding 1 of power transformer {name(tr)} connected to?",
                f"{name(tn)}",
                {"type": "entity", "value": name(tn)},
                2, f"{name(tr)}->end1->TN"))

# count loads / machines per substation (aggregation, >=2 hops)
for s in subs:
    n_loads = sum(1 for ld in loads if substation_of(ld) == s)
    if n_loads:
        s2_cands.append((
            f"How many energy consumers are located in substation {name(s)}?",
            f"{n_loads}",
            {"type": "count", "value": n_loads},
            2, f"count loads in {name(s)}"))
    n_m = sum(1 for m in machines if substation_of(m) == s)
    if n_m:
        s2_cands.append((
            f"How many synchronous machines operate in substation {name(s)}?",
            f"{n_m}",
            {"type": "count", "value": n_m},
            2, f"count machines in {name(s)}"))

# equipment sharing a TN with a busbar (3 hops: busbar->TN->equipment)
for b in busbars:
    btns = tns_of_eq(b)
    if btns:
        others = sorted(n2 for n2 in
                        (name(e) for e in tn_eqs[btns[0]] if e != b
                         and objects[e]["class"] in ("ACLineSegment", "PowerTransformer",
                                                     "SynchronousMachine", "EnergyConsumer",
                                                     "LinearShuntCompensator")))
        if len(others) >= 2:
            s2_cands.append((
                f"Which pieces of equipment are electrically connected to the same "
                f"topological node as busbar section {name(b)}? List their names.",
                ", ".join(others),
                {"type": "entity_set", "values": others},
                3, f"{name(b)}->TN->equipment"))

# region of machine (machine->VL->substation->region, 3 hops)
for m in machines:
    sub = substation_of(m)
    if sub:
        reg = region_of_substation(sub)
        s2_cands.append((
            f"In which geographical region does synchronous machine {name(m)} operate?",
            f"{reg}",
            {"type": "entity", "value": reg},
            3, f"{name(m)}->Sub->Region"))

# nominal voltage of a line's endpoint TN (line->TN->BaseVoltage)
for l in lines_:
    ltns = tns_of_eq(l)
    if ltns:
        kv = nominal_kv(ltns[0])
        if kv:
            s2_cands.append((
                f"What is the nominal voltage (in kV) of topological node {name(ltns[0])}, "
                f"to which AC line segment {name(l)} is connected?",
                f"{kv:g} kV",
                {"type": "number", "value": kv, "unit": "kV", "tol": 0.01},
                2, f"{name(l)}->TN->BaseVoltage"))

s2_sel = []
used_q = set()
for cand in itertools.chain(interleave(s2_cands, 3), s2_cands):
    if len(s2_sel) >= 25:
        break
    if cand[0] in used_q:
        continue
    used_q.add(cand[0])
    s2_sel.append(cand)
for (q, g, spec, hops, ev) in s2_sel:
    add_qa(q, g, spec, "S2", hops, ev)

print(f"QA items: {len(qa)} (S1={sum(1 for i in qa if i['stratum']=='S1')}, "
      f"S2={sum(1 for i in qa if i['stratum']=='S2')})")
assert len(qa) == 50, f"Expected 50 QA items, got {len(qa)}"

# ---------------------------------------------------------------------------
# 7. Save everything + H3 cost log
# ---------------------------------------------------------------------------
build_wall = time.time() - t0
(OUT / "g_std_nodes.json").write_text(json.dumps(nodes, indent=2))
(OUT / "g_std_edges.json").write_text(json.dumps(edges, indent=2))
(OUT / "g_std_support.json").write_text(json.dumps(support, indent=2))
(OUT / "cim_qa_items.json").write_text(json.dumps(qa, indent=2))
(OUT / "h3_g_std_cost.json").write_text(json.dumps({
    "method": "Direct CGMES RDF/XML parse (ENTSO-E MicroGrid BC Assembled, CGMES v2.4.15)",
    "wall_sec": build_wall,
    "llm_calls": 0,
    "llm_tokens": 0,
    "nodes": len(nodes),
    "edges": len(edges),
    "source": "ENTSO-E CGMES Conformity Assessment test configuration (via powsybl-core mirror)",
}, indent=2))

print(f"\nG_STD build complete in {build_wall:.3f}s (0 LLM calls). Outputs in {OUT}")
