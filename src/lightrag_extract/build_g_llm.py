# SPDX-License-Identifier: Apache-2.0
"""
run_lightrag_v2.py - G_LLM extraction over the CGMES-derived corpus, with
EXACT token accounting (fixes v1 limitation "token costs unmeasured").

LLM: Azure gpt-5.1 (same builder LLM as v1; logged per-call usage)
Embeddings: sentence-transformers all-MiniLM-L6-v2 (local)

Outputs:
  data/networks/microgrid/lightrag_workdir/        - LightRAG state (graphml is G_LLM)
  data/networks/microgrid/g_llm_entities.json
  data/networks/microgrid/g_llm_edges.json
  data/networks/microgrid/h3_g_llm_cost.json       - wall clock + calls + prompt/completion tokens

Usage: python3 -m src.lightrag_extract.build_g_llm
"""

import asyncio
import json
import pathlib
import re
import time
import urllib.request

import os
BASE = pathlib.Path(__file__).resolve().parent.parent.parent
DATA = pathlib.Path(os.environ.get("V2_DATA", BASE / "data" / "networks" / "microgrid"))
ENV = BASE / ".env"

env_text = ENV.read_text() if ENV.exists() else ""
def getenv(k):
    m = re.search(rf'^{k}=(.+)$', env_text, re.MULTILINE)
    return (m.group(1).strip() if m else os.environ.get(k, ""))

ENDPOINT = getenv("AZURE_OPENAI_ENDPOINT").rstrip("/")
AZURE_KEY = getenv("AZURE_OPENAI_API_KEY") or getenv("AZURE_OPENAI_KEY")
DEPLOYMENT = getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-5.1"
API_VERSION = getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"

# ---------------------------------------------------------------------------
# Token-accounting Azure LLM func
# ---------------------------------------------------------------------------
USAGE = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

def _azure_chat_sync(messages, max_tokens=4000):
    url = f"{ENDPOINT}/openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"
    payload = {"messages": messages, "max_completion_tokens": max_tokens}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"api-key": AZURE_KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    u = data.get("usage", {})
    USAGE["calls"] += 1
    USAGE["prompt_tokens"] += u.get("prompt_tokens", 0)
    USAGE["completion_tokens"] += u.get("completion_tokens", 0)
    USAGE["total_tokens"] += u.get("total_tokens", 0)
    return data["choices"][0]["message"]["content"]

async def azure_llm(prompt, system_prompt=None, history_messages=None, **kwargs):
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    for m in (history_messages or []):
        msgs.append(m)
    msgs.append({"role": "user", "content": prompt})
    return await asyncio.to_thread(_azure_chat_sync, msgs)

# ---------------------------------------------------------------------------
# Local embeddings
# ---------------------------------------------------------------------------
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from sentence_transformers import SentenceTransformer

_st = None
def _load_st():
    global _st
    if _st is None:
        _st = SentenceTransformer("all-MiniLM-L6-v2")
    return _st

async def local_embed(texts):
    return _load_st().encode(texts, show_progress_bar=False)

embedding_func = EmbeddingFunc(embedding_dim=384, func=local_embed, max_token_size=512)

# ---------------------------------------------------------------------------
async def main():
    corpus = (DATA / "corpus.txt").read_text()
    workdir = DATA / "lightrag_workdir"
    workdir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    rag = LightRAG(
        working_dir=str(workdir),
        llm_model_func=azure_llm,
        llm_model_name=DEPLOYMENT,
        embedding_func=embedding_func,
        entity_extract_max_gleaning=2,   # same as v1 (frozen)
        chunk_token_size=512,
        chunk_overlap_token_size=64,
    )
    await rag.initialize_storages()

    print(f"Inserting corpus ({len(corpus.split())} words)...")
    await rag.ainsert(corpus)
    wall = time.time() - t0
    print(f"Insert complete in {wall:.1f}s, {USAGE['calls']} LLM calls, "
          f"{USAGE['total_tokens']} tokens")

    # Export graph
    import networkx as nx
    graphml = workdir / "graph_chunk_entity_relation.graphml"
    G = nx.read_graphml(str(graphml))
    nodes_out = [{"id": n, "type": d.get("entity_type", "Unknown"),
                  "description": d.get("description", "")} for n, d in G.nodes(data=True)]
    edges_out = []
    for src, dst, d in G.edges(data=True):
        rel = d.get("keywords", d.get("relation_name", "RELATED_TO"))
        edges_out.append({"src": src, "rel": rel, "dst": dst,
                          "description": d.get("description", ""),
                          "weight": d.get("weight", 1.0)})
    (DATA / "g_llm_entities.json").write_text(json.dumps(nodes_out, indent=2))
    (DATA / "g_llm_edges.json").write_text(json.dumps(edges_out, indent=2))
    print(f"G_LLM: {len(nodes_out)} entities, {len(edges_out)} edges")

    (DATA / "h3_g_llm_cost.json").write_text(json.dumps({
        "method": "LightRAG 1.5.1 (Azure gpt-5.1 builder + local MiniLM embeddings)",
        "wall_sec": wall,
        "llm_calls": USAGE["calls"],
        "prompt_tokens": USAGE["prompt_tokens"],
        "completion_tokens": USAGE["completion_tokens"],
        "total_tokens": USAGE["total_tokens"],
        "corpus_words": len(corpus.split()),
        "nodes": len(nodes_out),
        "edges": len(edges_out),
    }, indent=2))
    print("H3 cost log saved.")

if __name__ == "__main__":
    asyncio.run(main())
