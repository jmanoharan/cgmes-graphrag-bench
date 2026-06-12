# SPDX-License-Identifier: Apache-2.0
"""
stats_v2.py - Pre-registered statistical analysis for H2 + H3 compilation.

H2: paired per-item contrast G_STD vs G_LLM on deterministic verdicts.
  * McNemar exact test (primary - appropriate for paired binary outcomes;
    registered Wilcoxon signed-rank also reported; deviation documented)
  * Holm correction across the 3 registered contrasts (All, S1, S2)
  * Judge agreement: Cohen's kappa (gpt-5.1 vs Claude Haiku, and each vs
    deterministic) - the judge-reliability harness from PROPOSAL.md step 6.

H3: compile build-cost contrast with exact token counts.

Usage: python3 -m src.scoring.stats
"""

import json
import math
import pathlib
from collections import defaultdict

import os
BASE = pathlib.Path(__file__).resolve().parent.parent.parent
DATA = pathlib.Path(os.environ.get("V2_DATA", BASE / "data" / "networks" / "microgrid"))

results = json.loads((DATA / "h2_results.json").read_text())

# pair up
by_item = defaultdict(dict)
for r in results:
    by_item[r["id"]][r["kg"]] = r

def mcnemar_exact(pairs):
    """pairs: list of (std_correct, llm_correct). Returns (b, c, p)."""
    b = sum(1 for s, l in pairs if s and not l)   # std right, llm wrong
    c = sum(1 for s, l in pairs if not s and l)   # std wrong, llm right
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n) * 2
    return b, c, min(1.0, p)

def wilcoxon_sign(pairs):
    """Registered Wilcoxon signed-rank; on paired binary data this reduces to
    a sign test on non-zero differences (all |diff|=1, tied ranks)."""
    diffs = [int(s) - int(l) for s, l in pairs if s != l]
    n = len(diffs)
    if n == 0:
        return 1.0
    pos = sum(1 for d in diffs if d > 0)
    k = min(pos, n - pos)
    p = sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n) * 2
    return min(1.0, p)

def cohen_kappa(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x != "ERROR" and y != "ERROR"]
    if not pairs:
        return None
    n = len(pairs)
    po = sum(1 for x, y in pairs if x == y) / n
    pa1 = sum(1 for x, _ in pairs if x == "CORRECT") / n
    pb1 = sum(1 for _, y in pairs if y == "CORRECT") / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe < 1 else None

def stratum_pairs(stratum=None):
    out = []
    for qid, arms in sorted(by_item.items()):
        if "std" not in arms or "llm" not in arms:
            continue
        if stratum and arms["std"]["stratum"] != stratum:
            continue
        out.append((arms["std"]["det_verdict"] == "CORRECT",
                    arms["llm"]["det_verdict"] == "CORRECT"))
    return out

contrasts = {}
raw_ps = {}
for label, stratum in [("All", None), ("S1", "S1"), ("S2", "S2")]:
    pairs = stratum_pairs(stratum)
    n = len(pairs)
    acc_std = sum(s for s, _ in pairs) / n
    acc_llm = sum(l for _, l in pairs) / n
    b, c, p_mcn = mcnemar_exact(pairs)
    p_wil = wilcoxon_sign(pairs)
    # Wald 95% CI on the paired accuracy difference (b-c)/n:
    # SE = sqrt(b + c - (b-c)^2/n) / n   (standard paired-proportions SE)
    se = math.sqrt(max(b + c - (b - c) ** 2 / n, 0)) / n
    delta = (acc_std - acc_llm)
    ci_lo, ci_hi = delta - 1.96 * se, delta + 1.96 * se
    contrasts[label] = {
        "n": n, "acc_std": round(acc_std, 4), "acc_llm": round(acc_llm, 4),
        "delta_pp": round(delta * 100, 1),
        "delta_ci95_pp": [round(ci_lo * 100, 1), round(ci_hi * 100, 1)],
        "mcnemar_b_std_only": b, "mcnemar_c_llm_only": c,
        "p_mcnemar_exact": round(p_mcn, 5), "p_wilcoxon_sign": round(p_wil, 5),
    }
    raw_ps[label] = p_mcn

# Holm correction across the 3 registered contrasts
ordered = sorted(raw_ps.items(), key=lambda kv: kv[1])
m = len(ordered)
holm = {}
prev = 0.0
for rank, (label, p) in enumerate(ordered):
    adj = min(1.0, max(prev, (m - rank) * p))
    prev = adj
    holm[label] = round(adj, 5)
for label in contrasts:
    contrasts[label]["p_holm"] = holm[label]
    contrasts[label]["significant_at_0.05_holm"] = holm[label] < 0.05

# Judge reliability harness
det = [r["det_verdict"] for r in results]
j1 = [r.get("judge_gpt51", "ERROR") for r in results]
j2 = [r.get("judge_claude_haiku", "ERROR") for r in results]
judges = {
    "kappa_gpt51_vs_claude": cohen_kappa(j1, j2),
    "kappa_det_vs_gpt51": cohen_kappa(det, j1),
    "kappa_det_vs_claude": cohen_kappa(det, j2),
    "judge_errors": sum(1 for x in j1 + j2 if x == "ERROR"),
}
judges = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in judges.items()}

# H3 compile
std_cost = json.loads((DATA / "h3_g_std_cost.json").read_text())
llm_cost = json.loads((DATA / "h3_g_llm_cost.json").read_text())
h3 = {
    "g_std": std_cost,
    "g_llm": llm_cost,
    "wall_ratio_llm_over_std": round(llm_cost["wall_sec"] / std_cost["wall_sec"], 1),
    "token_gap": f"{llm_cost['total_tokens']} vs 0",
    "note": "Wall ratio is dominated by cloud API latency; the structural point is "
            "0 LLM calls / 0 tokens for G_STD vs full corpus re-processing for G_LLM, "
            "which scales with corpus size.",
}

out = {"h2_contrasts": contrasts, "judge_reliability": judges, "h3": h3,
       "registered_mde_note": "Pre-registered MDE: n=50 -> ~23pp, n=25 (stratum) -> ~32pp "
                              "(Holm, alpha=0.05, power=0.80). Effects below MDE reported "
                              "as inconclusive regardless of nominal p."}
(DATA / "stats_v2.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
