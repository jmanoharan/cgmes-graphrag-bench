# Experiment Plan: Claim-Driven Roadmap

**Paper:** Standards-Native vs. LLM-Extracted KGs for Power-System GraphRAG.
**Scope authority:** `TOPIC.md` (frozen) · **Protocol:** `PROPOSAL.md` · **Review:** `SELF_REVIEW.md`.
**Compute:** 1× NVIDIA GB10 (local). Reader = open-weight (Qwen2.5-7B); builder LLM + judges via API.
**Generated:** 2026-06-10. This plan is execution-ready *once Step -1 and the gate pass.*

> **Reading order:** every experiment below maps to a pre-registered hypothesis (H1/H2/H3 in `TOPIC.md`).
> Nothing here introduces a claim not already registered. Steps run in order; each has an explicit
> **decision rule** and **kill condition**. The cheap, objective gate runs *before* any GPU spend.

---

## Claim → experiment → evidence matrix

| Claim | Experiment | Primary evidence (artifact) | Judge-dependent? | Kill condition |
|-------|-----------|-----------------------------|------------------|----------------|
| **H1** LLM invents wrong edges vs IEC schema | E2 (edge precision/recall) | `results/edge_precision.json` + endpoint/type split table | **No** | none - H1 is reportable any direction |
| **H2** G_STD matches/beats G_LLM on reasoning items | E3 (ElecBench S2 downstream) | `results/elecbench_downstream.json` | Yes (≥2 judges + human) | no S2 stratum → demote H2 to parity |
| **H3** G_STD ≈ zero build cost vs G_LLM | E1 (build-cost log) | `results/build_cost.json` | **No** | none |

---

## Phase 0: Preconditions (no GPU)

### Step -1: Retrievable-corpus precondition *(logically prior to the gate)*
- **Do:** clone ElecBench; determine whether a *retrievable corpus* exists (documents to index), not only QA pairs.
- **Decision:** corpus exists → continue. **No corpus** → trigger pre-registered pivot to a buildable
  grid-code/standards document corpus; **record loss of ElecBench-number comparability** in the paper.
- **Artifact:** `results/corpus_precheck.md` (what exists, decision taken).

### Step 0: Source the standard
- **Do:** obtain a public CGMES / IEC 61970 export (IEEE 14- or 39-bus CGMES test case) + IEC 61850
  logical-node reference. Parse to a typed-edge graph G_STD.
- **Artifact:** `data/gstd_graph.json` (entities, typed edges, provenance), `results/gstd_build.md`.

### GATE: CIM↔ElecBench entity-overlap pre-check  ⟵ **first thing that can kill the idea**
- **Do:** run the entity resolver (canonical mRID/IDs + name normalization) between ElecBench
  topology/protection entities and G_STD; manually adjudicate a sample; **double-annotate + report IAA**.
- **Also:** classify alignable items into **S1** (schema-lookup) and **S2** (reasoning/multi-hop).
- **Decision rule (frozen, exact):**
  - **GO** - ≥ 50 alignable items **and** ≥ 20 in S2.
  - **RESTRICT** - 20-49 alignable items: run on covered slice; H2 becomes a **parity** claim (drop "beat").
  - **DEMOTE** - < 20: abandon Idea 2, fall back to **Idea 1** (the flagship-backup in `IDEA_REPORT.md`).
- **Pre-gate task:** compute and freeze the **MDE** (`GAP_GATE_MDE` in `PROPOSAL.md` §3.6) - minimum
  detectable per-metric effect at n=50 and n=20, paired, α=.05 Holm-corrected, power=.8, using a judge-variance
  estimate from a 10-item judge test-retest.
- **Artifact:** `results/gate_overlap.json` (counts, S1/S2 split, IAA, decision). **Reported regardless of outcome.**

---

## Phase 1: Build (post-GO)

### E1: Build both graphs + cost log → **H3**
- **G_LLM:** LightRAG over the corpus (primary); MS GraphRAG secondary if budget allows. Log **tokens, LLM
  calls, wall-clock**.
- **G_STD:** already parsed (Step 0); ~zero LLM cost (parse-only). Load **into LightRAG's own graph store** so
  both use LightRAG's native retriever (resolves the "identical retriever" confound - see `PROPOSAL.md` §3.1).
- **Decision:** none (descriptive). **Artifact:** `results/build_cost.json`.
- **GPU:** minimal (extraction is API-bound). **<1h wall-clock.**

---

## Phase 2: Measure

### E2: Edge precision/recall vs schema → **H1** *(primary, judge-independent)*
- **Precision:** fraction of G_LLM edges (over aligned entity set) valid in G_STD; complement = hallucination/mislabel rate.
- **Recall:** against the **corpus-expressible** edge subset only; raw recall reported separately as coverage.
- **Decompose:** endpoint errors vs relation-type errors (diagnostic, per `SELF_REVIEW.md` strength #4).
- **Decision:** none (reportable any direction). **Artifact:** `results/edge_precision.json` + table.
- **GPU:** none (graph contrast). **<30 min.**

### E3: Downstream ElecBench → **H2**
- Both pipelines (G_LLM, G_STD), same reader, on the **S2 reasoning stratum** (primary) + S1 (sanity).
- Score all 6 ElecBench metrics with **≥2 judge models + human spot-check**; report *stability* as noise floor.
- **Paired** per-item tests, Holm-corrected across metrics; stratify S1/S2 and topology/protection.
- **Decision:** confirm/deny H2 on S2 factuality+security against the frozen MDE. **Artifact:** `results/elecbench_downstream.json`.
- **GPU:** Qwen2.5-7B inference over (items × 2 pipelines). **<2h.**

### E4: Judge-reliability harness *(runs alongside E3)*
- Test-retest on the judges + inter-judge agreement on a subset; report ElecBench *stability*.
- **Gates interpretation of E3.** **Artifact:** `results/judge_reliability.json`.

---

## Phase 3: Ablations (per `PROPOSAL.md` §3.5)

| Ablation | Question | Artifact |
|----------|----------|----------|
| **A1 Edge-label fidelity** | structure-only edges vs typed relations in reader context | `results/sensitivity study_labels.json` |
| **A2 Graph density** | does a denser G_LLM help downstream, or just add hallucinated edges? (links H1↔H2) | `results/sensitivity study_density.json` |
| **A3 Retriever design** | native LightRAG retrieval vs uniform custom retriever over both graphs (isolates retriever-attributable delta) | `results/sensitivity study_retriever.json` |

---

## Minimum first pilot (do this before anything else)

**The gate (Phase 0) on one public CGMES case.** No GPU, no graph build. It alone decides GO/RESTRICT/DEMOTE.
Pair it with the 10-item judge test-retest to freeze the MDE. If the gate says DEMOTE, **stop and pivot to
Idea 1** - do not spend GPU on E1-E4.

## GPU/time budget (post-GO, full study)

| Phase | GPU | Wall-clock |
|-------|-----|-----------|
| 0 Gate + precond | none | hours (manual alignment) |
| E1 build | minimal | <1h |
| E2 edge precision | none | <30m |
| E3 downstream | Qwen-7B inference | <2h |
| E4 judge harness | none (API) | parallel to E3 |
| Phase 3 sensitivity studys | Qwen-7B inference | <2h |
| **Total** | well within single-GB10 budget | **<6 GPU-h** |

## Deliverables checklist (feeds `PROPOSAL.md` DATA_NEEDED markers)

- [ ] `results/corpus_precheck.md` → unblocks everything (Step -1)
- [ ] `results/gate_overlap.json` → `GAP_GATE_MDE` + gate decision
- [ ] `results/build_cost.json` → `GAP_S6_COST` (H3)
- [ ] `results/edge_precision.json` → `GAP_S6_EDGE` (H1) **← the headline number**
- [ ] `results/elecbench_downstream.json` → `GAP_S6_DOWNSTREAM` (H2)
- [ ] `results/judge_reliability.json` → noise floor for H2
- [ ] `results/sensitivity study_*.json` → `GAP_S6_ABLATION`
- [ ] then: fill `PROPOSAL.md` §6, write `GAP_S6_DISCUSSION`, run `/paper-claim-audit`, re-review with a **non-Claude** reviewer

## Open items carried from SELF_REVIEW.md
- [x] `references.bib` ≥ 25 entries → **done (29 verified entries)**
- [ ] `GAP_GATE_MDE` - compute at gate time (needs judge-variance estimate)
- [ ] Non-Claude adversarial review before submission (cross-model invariant currently unmet)
