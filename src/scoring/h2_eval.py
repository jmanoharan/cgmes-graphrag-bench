# SPDX-License-Identifier: Apache-2.0
"""
eval_h2_v2.py - H2 downstream QA evaluation, protocol-compliant version.

Fixes v1 confounds:
  * SYMMETRIC retrieval - one code path for both graphs: seed entities found by
    matching each graph's OWN node names against the question, 2-hop expansion,
    uniform triple rendering, identical char cap. NO per-graph answer tables.
  * Reader = Qwen2.5-7B-Instruct, LOCAL (the pre-registered reader; v1 used
    gpt-5.1, an unregistered deviation).
  * PRIMARY scoring is deterministic (answer_spec machine check). LLM judges are
    SECONDARY: two independent cross-family models (Azure gpt-5.1 + Claude Haiku),
    judge != reader family, agreement (Cohen's kappa) reported.

Outputs: data/networks/microgrid/h2_results.json (per-item), data/networks/microgrid/h2_summary.json

Usage:
  python3 -m src.scoring.h2_eval            # full run
  python3 -m src.scoring.h2_eval --limit 4  # smoke test
  python3 -m src.scoring.h2_eval --no-judges  # deterministic scoring only
"""

import argparse
import json
import pathlib
import re
import time
import urllib.request
from collections import defaultdict

import os
BASE = pathlib.Path(__file__).resolve().parent.parent.parent
DATA = pathlib.Path(os.environ.get("V2_DATA", BASE / "data" / "networks" / "microgrid"))
ENV = BASE / ".env"

env_text = ENV.read_text() if ENV.exists() else ""
def getenv(k):
    m = re.search(rf'^{k}=(.+)$', env_text, re.MULTILINE)
    return (m.group(1).strip() if m else os.environ.get(k, ""))

# ---------------------------------------------------------------------------
# Graph loading: both graphs into ONE uniform representation
# ---------------------------------------------------------------------------
def load_g_std():
    nodes = json.loads((DATA / "g_std_nodes.json").read_text())
    edges = json.loads((DATA / "g_std_edges.json").read_text())
    by_id = {}
    for n in nodes:
        attrs = " ".join(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}"
                         for k, v in n["attrs"].items() if k != "description")
        label = n["name"] or n["mrid"][:8]
        by_id[n["id"]] = {"label": label, "desc": f"{label} ({n['class']}) {attrs}".strip()}
    adj = defaultdict(list)
    for e in edges:
        if e["src"] in by_id and e["dst"] in by_id:
            adj[e["src"]].append((e["rel"], e["dst"]))
            adj[e["dst"]].append((e["rel"], e["src"]))
    return by_id, adj

def load_g_hyb():
    """G_HYB (exploratory, post-hoc - disclosed): deterministic semantic compression
    of G_STD. Nodes = CIM objects with attributes; edges = the five derived support
    relations (shared-TN connectivity, transitive containment, composition, voltage)
    instead of raw Terminal-indirected associations. Zero LLM involvement."""
    nodes = json.loads((DATA / "g_std_nodes.json").read_text())
    support = json.loads((DATA / "g_std_support.json").read_text())
    by_id = {}
    for n in nodes:
        attrs = " ".join(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}"
                         for k, v in n["attrs"].items() if k != "description")
        label = n["name"] or n["mrid"][:8]
        by_id[n["id"]] = {"label": label, "desc": f"{label} ({n['class']}) {attrs}".strip()}
    adj = defaultdict(list)
    for s in support:
        if s["a"] in by_id and s["b"] in by_id:
            adj[s["a"]].append((s["rel"], s["b"]))
            adj[s["b"]].append((s["rel"], s["a"]))
    # Terminals/raw indirection nodes carry no support edges and are dropped naturally
    return by_id, adj

def load_g_llm():
    import networkx as nx
    G = nx.read_graphml(str(DATA / "lightrag_workdir" / "graph_chunk_entity_relation.graphml"))
    by_id = {}
    for n, d in G.nodes(data=True):
        desc = d.get("description", "")[:150]
        etype = d.get("entity_type", "?")
        by_id[n] = {"label": n, "desc": f"{n} ({etype}) {desc}".strip()}
    adj = defaultdict(list)
    for s, t, d in G.edges(data=True):
        rel = d.get("keywords", d.get("relation_name", "related_to"))
        adj[s].append((rel, t))
        adj[t].append((rel, s))
    return by_id, adj

# ---------------------------------------------------------------------------
# SYMMETRIC retrieval (single code path; only the graph differs)
# ---------------------------------------------------------------------------
CTX_CAP = 8000  # chars, identical for both arms

def norm_text(s):
    s = s.lower()
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def find_seeds(question, by_id):
    """Nodes whose name appears in the question (case/sep-insensitive).
    Purely numeric names are skipped (CGMES names some voltage levels '220.0',
    which would spuriously match '220 kV' in question text). Same rule both arms."""
    qn = norm_text(question)
    seeds = []
    for nid, info in by_id.items():
        label = info["label"]
        if re.fullmatch(r"[\d.]+", label):
            continue
        if len(label) < 3:
            continue
        if norm_text(label) in qn:
            seeds.append(nid)
    # prefer longer (more specific) matches first; dedup nested matches kept - harmless
    seeds.sort(key=lambda x: -len(by_id[x]["label"]))
    return seeds[:6]

def degree_fallback(by_id, adj):
    return sorted(by_id, key=lambda n: -len(adj.get(n, [])))[:5]

def retrieve(question, by_id, adj, hops=2):
    seeds = find_seeds(question, by_id)
    fallback = not seeds
    if fallback:
        seeds = degree_fallback(by_id, adj)
    visited, frontier = set(), set(seeds)
    triples = []
    for _ in range(hops):
        nxt = set()
        for nid in frontier:
            if nid in visited:
                continue
            visited.add(nid)
            for rel, nbr in adj.get(nid, []):
                triples.append((nid, rel, nbr))
                if nbr not in visited:
                    nxt.add(nbr)
        frontier = nxt
    visited |= frontier

    lines = ["Knowledge graph context:", "", "Entities:"]
    for nid in sorted(visited):
        if nid in by_id:
            lines.append(f"  {by_id[nid]['desc']}")
    lines.append("")
    lines.append("Relations:")
    seen = set()
    for s, rel, t in triples:
        key = (s, rel, t) if s <= t else (t, rel, s)
        if key in seen:
            continue
        seen.add(key)
        rel_short = str(rel)[:60]
        lines.append(f"  {by_id[s]['label']} --[{rel_short}]--> {by_id[t]['label']}")
    ctx = "\n".join(lines)
    if len(ctx) > CTX_CAP:
        ctx = ctx[:CTX_CAP] + "\n[context truncated]"
    return ctx, len(seeds), fallback

# ---------------------------------------------------------------------------
# Reader: Qwen2.5-7B-Instruct, local (pre-registered)
# ---------------------------------------------------------------------------
READER_SYSTEM = (
    "You are a power systems expert. Answer the question using ONLY the provided "
    "knowledge graph context. Be precise with names and numeric values, and include "
    "units. If the context does not contain sufficient information, say "
    "\"I cannot determine this from the provided context.\" "
    "Keep your answer to 1-3 sentences.")

_reader = None
def load_reader():
    global _reader
    if _reader is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        name = "Qwen/Qwen2.5-7B-Instruct"
        print("Loading Qwen2.5-7B-Instruct (local reader)...")
        tok = AutoTokenizer.from_pretrained(name)
        model = AutoModelForCausalLM.from_pretrained(
            name, dtype=torch.bfloat16, device_map="cuda")
        model.eval()
        _reader = (tok, model)
    return _reader

def answer_question(context, question):
    import torch
    tok, model = load_reader()
    messages = [
        {"role": "system", "content": READER_SYSTEM},
        {"role": "user", "content": f"{context}\n\nQuestion: {question}\nAnswer:"},
    ]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok([text], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=160, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

# ---------------------------------------------------------------------------
# PRIMARY deterministic scoring via answer_spec
# ---------------------------------------------------------------------------
WORD_NUMS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

def extract_numbers(text):
    nums = [float(x.replace(",", "")) for x in
            re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)]
    for w, v in WORD_NUMS.items():
        if re.search(rf"\b{w}\b", text.lower()):
            nums.append(float(v))
    return nums

def det_verdict(spec, prediction):
    p = prediction.strip()
    if not p:
        return "INCORRECT"
    if "cannot determine" in p.lower():
        return "INCORRECT"
    t = spec["type"]
    if t == "number":
        gold = float(spec["value"])
        tol = spec.get("tol", 0.01)
        thresh = max(abs(gold) * tol, 1e-9) if gold != 0 else 1e-9
        return "CORRECT" if any(abs(x - gold) <= thresh for x in extract_numbers(p)) else "INCORRECT"
    if t == "entity":
        return "CORRECT" if norm_text(spec["value"]) in norm_text(p) else "INCORRECT"
    if t == "entity_set":
        pn = norm_text(p)
        return "CORRECT" if all(norm_text(v) in pn for v in spec["values"]) else "INCORRECT"
    if t == "count":
        gold = float(spec["value"])
        return "CORRECT" if any(abs(x - gold) < 1e-9 for x in extract_numbers(p)) else "INCORRECT"
    return "INCORRECT"

# ---------------------------------------------------------------------------
# SECONDARY LLM judges (two independent model families, neither = reader)
# ---------------------------------------------------------------------------
JUDGE_SYSTEM = """You are an expert evaluator. Given a question, the gold answer, and a model answer, decide if the model answer is factually correct.
Allow ±1% numeric tolerance and naming variants (underscores/hyphens/spaces are interchangeable; case-insensitive).
Respond with exactly one word: CORRECT or INCORRECT."""

def judge_azure(question, gold, pred):
    url = (f"{getenv('AZURE_OPENAI_ENDPOINT').rstrip('/')}/openai/deployments/"
           f"epriai-prod-tech-gpt-5-1/chat/completions?api-version=2024-12-01-preview")
    payload = {"messages": [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": f"Question: {question}\nGold answer: {gold}\nModel answer: {pred}\nVerdict:"}],
        "max_completion_tokens": 800}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"api-key": getenv("AZURE_OPENAI_KEY"),
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())["choices"][0]["message"]["content"].strip().upper()
    return "CORRECT" if out.startswith("CORRECT") else "INCORRECT"

def judge_claude(question, gold, pred):
    """Second judge: Claude Haiku via CLI (independent model family; the
    intended OpenAI judge key has no quota - documented in DEVIATIONS.md)."""
    import subprocess
    prompt = (f"{JUDGE_SYSTEM}\n\nQuestion: {question}\nGold answer: {gold}\n"
              f"Model answer: {pred}\nVerdict:")
    out = subprocess.run(
        ["claude", "-p", "--model", "haiku"],
        input=prompt, capture_output=True, text=True, timeout=120,
    ).stdout.strip().upper()
    return "CORRECT" if "CORRECT" in out and "INCORRECT" not in out else "INCORRECT"

def safe(fn, *a):
    for attempt in range(3):
        try:
            return fn(*a)
        except Exception as e:
            if attempt == 2:
                print(f"    judge error ({fn.__name__}): {e}")
                return "ERROR"
            time.sleep(2 * (attempt + 1))

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--kg", choices=["std", "llm", "hyb", "both"], default="both",
                    help="arms to evaluate (hyb = exploratory derived-compression arm)")
    ap.add_argument("--no-judges", action="store_true")
    ap.add_argument("--hops", type=int, default=2, help="retrieval expansion depth (sensitivity study)")
    ap.add_argument("--stratum", choices=["S1", "S2"], default=None, help="restrict to one stratum")
    ap.add_argument("--out-suffix", default="", help="suffix for output filenames")
    args = ap.parse_args()

    qa = json.loads((DATA / "cim_qa_items.json").read_text())
    if args.stratum:
        qa = [i for i in qa if i["stratum"] == args.stratum]
    if args.limit:
        qa = qa[:args.limit]

    arms = ("std", "llm") if args.kg == "both" else (args.kg,)
    loaders = {"std": load_g_std, "llm": load_g_llm, "hyb": load_g_hyb}
    graphs = {k: loaders[k]() for k in arms}
    for k, (by_id, adj) in graphs.items():
        print(f"G_{k.upper()}: {len(by_id)} nodes")

    results = []
    t_start = time.time()
    for i, item in enumerate(qa):
        for kg in arms:
            by_id, adj = graphs[kg]
            ctx, n_seeds, fallback = retrieve(item["question"], by_id, adj, hops=args.hops)
            t0 = time.time()
            pred = answer_question(ctx, item["question"])
            latency = time.time() - t0
            det = det_verdict(item["answer_spec"], pred)
            rec = {"id": item["id"], "stratum": item["stratum"], "kg": kg,
                   "question": item["question"], "gold": item["gold_answer"],
                   "predicted": pred, "det_verdict": det,
                   "n_seeds": n_seeds, "seed_fallback": fallback,
                   "context_chars": len(ctx), "latency_s": round(latency, 2)}
            if not args.no_judges:
                rec["judge_gpt51"] = safe(judge_azure, item["question"], item["gold_answer"], pred)
                rec["judge_claude_haiku"] = safe(judge_claude, item["question"], item["gold_answer"], pred)
            results.append(rec)
            print(f"[{i+1:02d}/{len(qa)}] {item['id']} {kg:>3} det={det:<9} "
                  f"({latency:.1f}s) {pred[:70]!r}")

    (DATA / f"h2_results{args.out_suffix}.json").write_text(json.dumps(results, indent=2))
    print(f"\nDone in {(time.time()-t_start)/60:.1f} min. Per-item results saved.")

    # summary
    summary = []
    for kg in arms:
        sub = [r for r in results if r["kg"] == kg]
        def acc(rows, key="det_verdict"):
            return (sum(1 for r in rows if r[key] == "CORRECT") / len(rows)) if rows else None
        s1 = [r for r in sub if r["stratum"] == "S1"]
        s2 = [r for r in sub if r["stratum"] == "S2"]
        entry = {"kg": kg, "n": len(sub),
                 "det_acc_all": acc(sub), "det_acc_s1": acc(s1), "det_acc_s2": acc(s2)}
        if not args.no_judges:
            entry |= {"gpt51_acc_all": acc(sub, "judge_gpt51"),
                      "claude_haiku_acc_all": acc(sub, "judge_claude_haiku")}
        summary.append(entry)
    (DATA / f"h2_summary{args.out_suffix}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
