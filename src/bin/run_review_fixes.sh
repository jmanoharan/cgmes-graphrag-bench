#!/usr/bin/env bash
# Serialized pipeline for the post-review experiments:
#   M-1: SmallGrid replication (build + H1 + H2)
#   M-2: two independent MicroGrid variance builds (stochastic LightRAG)
#   M-3: 3-hop ablation on the MicroGrid S2 stratum (deterministic scoring only)
#
# Run from the repository root:
#   bash src/bin/run_review_fixes.sh
#
# Requires LightRAG-builder API credentials (see docs/REPRODUCE.md). If credentials
# are not available, the cached lightrag_workdir/ directories under
# data/networks/*/ already contain the built graphs and can be scored directly.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "=== [M-1] SmallGrid LightRAG build ==="
V2_DATA=data/networks/smallgrid python3 -m src.lightrag_extract.build_g_llm

echo "=== [M-1] SmallGrid H1 scoring ==="
V2_DATA=data/networks/smallgrid python3 -m src.scoring.h1_edge_classifier

echo "=== [M-2] MicroGrid variance build 1/2 ==="
mkdir -p data/networks/microgrid_var1 data/networks/microgrid_var2
for v in microgrid_var1 microgrid_var2; do
  cp data/networks/microgrid/corpus.txt \
     data/networks/microgrid/g_std_nodes.json \
     data/networks/microgrid/g_std_edges.json \
     data/networks/microgrid/g_std_support.json \
     "data/networks/$v/" 2>/dev/null || true
done
V2_DATA=data/networks/microgrid_var1 python3 -m src.lightrag_extract.build_g_llm
V2_DATA=data/networks/microgrid_var1 python3 -m src.scoring.h1_edge_classifier

echo "=== [M-2] MicroGrid variance build 2/2 ==="
V2_DATA=data/networks/microgrid_var2 python3 -m src.lightrag_extract.build_g_llm
V2_DATA=data/networks/microgrid_var2 python3 -m src.scoring.h1_edge_classifier

echo "=== [M-1] SmallGrid H2 eval (with secondary judges) ==="
V2_DATA=data/networks/smallgrid python3 -m src.scoring.h2_eval

echo "=== [M-3] MicroGrid 3-hop ablation on S2 (deterministic only) ==="
V2_DATA=data/networks/microgrid python3 -m src.scoring.h2_eval \
    --hops 3 --stratum S2 --no-judges --out-suffix _hop3_s2

echo "ALL REVIEW-FIX RUNS COMPLETE"
