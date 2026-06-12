# Pre-Registration & Proposal

**Standards-Native vs. LLM-Extracted Knowledge Graphs for Power-System GraphRAG:
Measuring Graph-Construction Error Against the IEC/CIM Schema**

**Type:** Pre-registration (no experiments have been run; results sections carry `<!-- DATA_NEEDED -->`
markers and are intentionally empty). **Target venue (updated):** IEEE PESGM / IEEE Transactions on Smart Grid
(primary); ISWC / ESWC / AKBC (secondary - CIM-as-ontology angle); AI-for-energy workshops at NeurIPS/ICLR
(tertiary). *NeurIPS D&B and ACL main tracks are demoted - domain application papers score low on novelty
there; the power-domain and industrial-standard framing is best received in IEEE PES and semantic-web venues.*
**Generated:** 2026-06-10 · **Scope authority:** `paper-stage/TOPIC.md` (frozen).

> **Honesty banner.** This document pre-registers a study; it does not report findings. Every quantitative
> claim below is a *hypothesis to be tested*, never a result. Numbers like "X%" are placeholders. This
> proposal has been reviewed by **two adversarial passes**: (1) a same-family Claude reviewer (advisory;
> `SELF_REVIEW.md` round 1), and (2) an **independent external reviewer using OpenAI gpt-5.1 via Azure**
> (cross-model independence invariant satisfied; `EXTERNAL_REVIEW.md`). Both rounds' must-fix items have
> been applied; see `SELF_REVIEW.md` for the full changelog.
>
> **Gate update (2026-06-10).** Step -1 precondition executed: ElecBench's public GitHub release contains
> **288 QA pairs only** (partial open-source; full 34,030-entry dataset not released), with no source
> documents and no CIM-topology-answerable items. Step -1 NO-GO triggered. **H2 has been redesigned**:
> downstream evaluation now uses a **custom CIM-QA set** derived from the same CGMES case used for H1/G_STD,
> released as a paper artifact. Full decision trace in `GATE_REPORT.md`.

---

## Abstract

Graph-based Retrieval-Augmented Generation (GraphRAG) is increasingly proposed for technical,
relation-dense domains, and power systems - components → protection schemes → grid codes → topology - are a
natural fit. Almost universally, the graph is **extracted from text by an LLM**. Yet power systems are
unusual: they already ship a *curated, machine-readable, schema-correct* relational model in the form of
IEC 61970/CIM (CGMES) network models and IEC 61850 logical-node structure. This raises a question nobody has
tested: in a safety-critical domain, is an LLM-extracted graph actually better than the standard that already
exists - and how often does the LLM invent edges that the standard says are wrong? We pre-register a
controlled study that (1) builds two graphs over the same power corpus - an LLM-extracted KG and a
**standards-native** graph loaded directly from CGMES + IEC 61850 with zero LLM extraction - and wires both
into an identical retriever + reader; (2) introduces a **judge-independent edge-precision metric** that scores
the LLM graph against the IEC schema as ground truth, quantifying the fraction of hallucinated or mislabeled
edges; and (3) compares downstream answer quality on a **custom CIM-QA evaluation set** (50 items, ≥20 S2,
derived from the same CGMES case, released as a paper artifact) while logging graph-build cost as a
first-class axis. *Note: ElecBench's public release (288 partial items) contains no source corpus and
no CIM-topology-answerable items; the Step -1 gate triggered the pre-registered pivot to custom CIM-QA.* The study is designed to be informative regardless of outcome: a high
LLM edge-error rate indicts LLM graph extraction for safety-critical power use, while a low one validates it.
We also release the standards-native graph builder as a reusable artifact.

<!-- DATA_NEEDED: GAP_ABSTRACT_RESULTS - one-sentence headline result (edge-error rate + downstream verdict) once experiments run -->

## 1. Introduction

**The shift the field already made.** GraphRAG's reputation has moved from "graphs win" to "graphs win
*conditionally*." Microsoft's foundational GraphRAG (Edge et al., 2024) only ever claimed gains on *global,
query-focused summarization*, not factoid accuracy. The 2025-26 benchmarking wave then showed that on
ordinary accuracy GraphRAG frequently *underperforms* vanilla RAG, and that its edge largely vanishes once
retrieval becomes agentic. The positive evidence clusters in relational, jargon-dense engineering domains
(telecom O-RAN; manufacturing document QA), where explicit entity relationships that flat chunking fragments
are exactly what graphs preserve. Power systems are the canonical instance of such a domain, and now have a
real benchmark - **ElecBench** (Zhou et al., 2024): 24 datasets, 34,030 entries, scored on six metrics
(factuality, logicality, stability, security, fairness, expressiveness).

**The blind spot.** In essentially all of this work, the knowledge graph is *constructed by an LLM from
text*. The implicit assumptions are (a) the graph *must* be LLM-built, and (b) a denser, richer LLM graph is
better. Power is the one domain where both assumptions are directly testable, because a correct relational
model already exists as an engineering standard: CIM/IEC 61970 (and its CGMES exchange profiles) encodes the
network's components and topology; IEC 61850 encodes substation logical-node structure. Independent evidence
suggests caution about LLM-built graphs in general - recent work asks whether LLMs are effective KG
constructors and finds they are strong on relevance but weak on accuracy/completeness (Chen et al., 2025)  - 
but **no published work evaluates LLM-extracted power KGs against the CGMES/IEC schema as ground truth.**

**This proposal.** We treat the standard as an oracle for graph structure and ask three questions:

1. **(H1, objective - source-comparability)** Given the *same underlying corpus* that describes the
   power network, how faithfully does an LLM recover the CIM relational structure versus the structure
   encoded in the IEC/CGMES standard that describes the *same network*? We measure this as edge
   precision/recall against the schema, decomposed by error type (Type A: contradicts schema; Type C:
   no textual warrant; Type B: corpus-consistent but not in export - reported separately, not counted
   as failure). **Framing note:** G_STD is a CIM export; of course it wins on edge-precision-vs-CIM  - 
   that is *definitionally true* and is not the interesting claim. The interesting claim is *how large
   the LLM extraction gap is* and *which error types dominate*, as a calibration of LLM KG construction
   quality in safety-critical power use.
2. **(H2, downstream - revised after Step -1 gate)** Wired into an identical GraphRAG pipeline, does a
   standards-native graph *match or beat* the LLM-extracted KG on a **custom CIM-QA evaluation set**
   (50 items derived from the same CGMES case, ≥20 in S2 reasoning stratum, released as a paper artifact)?
   *Original design tested on ElecBench topology/protection; Step -1 gate (2026-06-10) found ElecBench's
   public release has no source corpus and no CIM-topology-answerable items - pivot to custom CIM-QA is
   the pre-registered fallback. See `GATE_REPORT.md`.*
3. **(H3, objective)** What is the build-cost gap (tokens, LLM calls, wall-clock) between the two?

**Contributions.**
- **C1.** A judge-independent *edge-precision-against-schema* metric for power-domain GraphRAG, with an
  entity-alignment protocol between free-text corpora and CGMES/IEC 61850.
- **C2.** The first controlled head-to-head of a **standards-native** graph vs. an LLM-extracted KG inside one
  power GraphRAG pipeline on a custom CIM-QA set, with build cost as a first-class axis.
- **C3.** A reusable standards-native graph builder (CGMES + IEC 61850 → retrievable graph) released as an artifact.
- **C4.** A pre-registered, NO-GO-aware protocol: if public CIM coverage of ElecBench is insufficient, that
  negative coverage finding is itself reported.

## 2. Related Work (positioning)

**Power-domain RAG.** *HG-RAG* (MDPI Electronics 15(7):1445, 2026) is the closest in-domain prior art - a
hierarchical graph-enhanced RAG for power systems with expert-reviewed QA - but its graph is LLM/hierarchy-built
and it never uses an engineering standard as ground truth, nor isolates standards-native vs LLM-extracted
construction. *GridCodex* (Shi et al., 2025, arXiv:2508.12682) targets grid-code reasoning/compliance but uses
**vector** RAG (RAPTOR), not a graph. Earlier power-KG QA (Tang et al., 2021) predates LLM-RAG. None compares
graph *construction source* against a standard.

**GraphRAG, conditionally.** Edge et al. (2024, arXiv:2404.16130) establish GraphRAG for global
summarization. Benchmarking work (GraphRAG-Bench / "When to use Graphs in RAG," 2025-26; "Do We Still Need
GraphRAG?", 2026) shows accuracy wins are task-conditional and shrink under agentic retrieval. LightRAG (2024,
arXiv:2410.05779) and HippoRAG (2024, arXiv:2405.14831) are cheaper graph-retrieval designs we can use as the
LLM-extracted baseline. Engineering-domain positives (O-RAN hybrid; manufacturing Document-GraphRAG) motivate
the power test bed.

**LLMs as KG constructors.** Chen et al. (2025, arXiv:2510.11297) and adjacent work (arXiv:2502.05239)
evaluate LLM KG construction in the *general* domain and find accuracy/completeness weaknesses, but never
against a curated engineering schema. *Toward Robust GraphRAG* (Ma et al., 2026, arXiv:2603.14828) does
controlled KG-issue injection and shows relation seeds reduce drift - adjacent to our edge analysis but it does
not score against a real standard, and is not power-specific.

**The gap we fill - and how we differ from the closest prior work.**

*Text2KGBench* (Mihindukulasooriya et al., 2023) is the open-domain template for evaluating LLM KG
extraction against a ground-truth ontology; a hostile reviewer's first move is "this is Text2KGBench on
power with a CIM oracle." Our defensible delta is a three-way combination none of the prior work shares:
(1) **the oracle is a real deployed engineering standard** (CGMES/IEC 61970, IEC 61850) that utilities
actually run on - not Wikidata, a thesaurus, or a synthetic perturbation; (2) **source-controlled
construction inside one end-to-end GraphRAG pipeline** with downstream QA evaluation; and (3) **build
cost as a first-class axis**, since the standards-native graph eliminates LLM extraction entirely.
Clinical-domain ontology-grounded GraphRAG (2026) and general LLM-KG-construction evaluation (Chen et al.,
2025; arXiv:2510.11297) share the evaluation-against-schema idea but not the industrial-standard oracle nor
the pipeline context nor the safety-critical deployment motivation.

*HG-RAG* (MDPI Electronics 15(7):1445, 2026) is our closest in-domain prior art - hierarchical
graph-enhanced RAG for power systems, LLM-extracted KG, power QA benchmark. It does **not** compare
LLM-extracted graphs against a standards-native baseline, does not use CIM/IEC as a ground-truth oracle,
and does not measure build cost. Its existence confirms the domain is live; our contribution is the
**construction-source contrast** and **schema-grounded evaluation** that HG-RAG does not do.

<!-- DATA_NEEDED: GAP_S2_CITES - add Text2KGBench full citation (Mihindukulasooriya et al., ISWC 2023) and clinical ontology-GraphRAG 2026 to references.bib -->

## 3. Method & Protocol

### 3.1 Two graphs, one pipeline
Over a single fixed power corpus aligned to a public network case:
- **G_LLM** - LLM-extracted KG via LightRAG (primary) and, budget permitting, MS GraphRAG (secondary), using
  one builder LLM with all tokens/calls/wall-clock logged.
- **G_STD** - standards-native graph loaded **directly** from a public CGMES / IEC 61970 export (e.g., the
  IEEE 14-/39-bus CGMES test case) plus IEC 61850 logical-node structure. **Zero** LLM extraction.

Both graphs feed the **same** open-weight reader (Qwen2.5-7B on the GB10). **Retrieval configuration
(frozen - identical across both conditions):**
- **Graph store:** G_STD is loaded into LightRAG's own graph store using the same ingestion API as G_LLM;
  both use LightRAG's native dual-level retrieval (keyword + community summaries).
- **Community detection:** identical algorithm (Leiden) and resolution parameter λ for both graphs.
- **Prompt templates:** identical system and query prompts, same context-window limit (4096 tokens).
- **Chunking:** same chunk size and overlap applied to the same corpus for both conditions; G_STD adds
  graph edges but does not alter the text chunks.
- **Retriever sensitivity study (A3):** a uniform BM25+1-hop expansion retriever is additionally run over both
  graphs, providing a retrieval-design-independent measurement of the graph-source effect.
Any deviation from these frozen parameters between conditions is a protocol violation and must be reported.
Only the **graph edge set** differs between G_LLM and G_STD.

### 3.2 Primary metric: edge precision/recall vs schema (judge-independent)

**Edge taxonomy (frozen - three mutually exclusive categories, all reported separately):**
We distinguish three types of G_LLM edges over the aligned entity set, each with a different interpretation:
- **Type A - Schema-contradictory:** edge whose endpoints or relation type directly violates the CGMES/IEC
  model (e.g., a voltage-level connected to a protection logical-node in a way the standard forbids). *Counted
  as a hallucination in H1.*
- **Type B - Schema-absent but corpus-consistent:** edge whose endpoints are aligned, the relation is
  *expressed in the text corpus*, but the standard does not encode it (either below CIM's abstraction level
  or in an extension not in the public CGMES sample). *Counted as unverifiable - excluded from H1 precision
  denominator; reported separately as a coverage gap.*
- **Type C - Absent from both:** edge with no textual warrant and no schema backing. *Counted as a
  hallucination in H1.*

H1 precision = (aligned edges that are Type A or C) / (all aligned edges). This operationalization is frozen
and applied identically regardless of outcome.

**Entity-alignment protocol (fully algorithmic, frozen before any system outputs are seen):**
1. Primary key: canonical mRID (CIM-standard UUID) where present.
2. Fallback: normalized name string (lowercase, stripped of punctuation, resolved by Levenshtein distance
   ≤ 2 to a unique CGMES entry; ambiguous cases → unaligned, excluded from scoring, coverage reported).
3. Ambiguous-name policy: if ≥ 2 CGMES entities match within distance 2 (e.g., multiple "Bus 1" in a
   multi-feeder topology), the entity is *not aligned* and its edges are excluded from precision/recall.
   Count of excluded-due-to-ambiguity entities is reported.
4. **Double-annotate a 20-entity sample** with a second annotator; report Fleiss' κ; if κ < 0.7, fix the
   algorithm before running the full alignment.
Only edges over the *uniquely aligned* entity set are scored.

**Corpus-expressible edge subset (frozen definition):**
An edge relation type is "corpus-expressible" if the text corpus contains ≥ 1 explicit relational statement
of that type (e.g., "Bus A connects to Line B") for any pair of aligned entities, as identified by a
pattern-matched extraction pass run *before* G_LLM is built and *before* seeing edge scores. Edge recall
is reported only against the corpus-expressible subset. Full recall against the complete CGMES export is
reported separately, labeled as **corpus↔schema coverage rate**, not LLM failure.

**Scoring:**
- **Edge precision** = (Type A + Type C edges) / (all aligned edges) - *the H1 headline number*.
- **Edge recall** = fraction of schema edges recovered by G_LLM, over the corpus-expressible + aligned subset.
- Report endpoint errors (Type A/C) vs relation-type errors separately for diagnostic depth.

### 3.3 Downstream: Custom CIM-QA evaluation (H2, revised after Step -1 gate)

**Gate outcome:** ElecBench's public release (2026-06-10 audit, `GATE_REPORT.md`) contains 288 QA pairs,
no source corpus documents, and zero CIM-topology-answerable items. Step -1 NO-GO; pre-registered pivot
to custom CIM-QA activated.

**Custom CIM-QA set construction:**
- Derive 50 QA items directly from the ground-truth CGMES export used for G_STD.
- Items cover: nominal voltage lookups, equipment connectivity, protection-scheme paths, multi-hop
  reasoning across zones/levels.
- Items are **author-generated** and released with the paper for full replication; this is disclosed as a
  limitation (internal construction, not independent benchmark) but provides the only tractable path when
  ElecBench data is unavailable.

**Anti-confound stratification (S1/S2 - unchanged algorithm):**
- **S1 (schema-lookup):** answer resolvable by a single-hop CGMES traversal; labeled by the pre-built
  resolver, answer-blind, before any pipeline is invoked.
- **S2 (reasoning):** ≥ 2 hops, or spans corpus text + graph, or involves protection-scheme logic not
  encoded as a direct topology edge. Items whose hop-count is indeterminate → assigned S2 (conservative).
- S1/S2 labels frozen before any system output is seen. No recategorization permitted.
- **H2 is tested primarily on S2**; S1 reported as sanity check only. If S2 < 20 items, H2 demoted to
  parity claim.

**Scoring:**
- Primary metrics: edge-precision-aligned QA accuracy (G_STD vs G_LLM), decomposed by S1/S2.
- Secondary: 3 judge models + human spot-check on 10 items; report judge agreement (κ).
- Paired significance tests (Wilcoxon signed-rank, Holm correction); stratified S1 vs S2.

**ElecBench (retained as Related Work context only):**
The original intent was to benchmark on ElecBench. Per the gate, that benchmark is inaccessible for this
use. ElecBench is retained in related work as the state-of-the-art power-domain LLM evaluation; the loss
of direct ElecBench contrast is a named limitation.

### 3.4 Build cost (H3)
Log tokens, LLM calls, and wall-clock to build each graph; report as a first-class axis alongside accuracy.

### 3.5 Ablations
- **Edge-label fidelity:** structure-only edges vs typed relations injected into the reader context.
- **Graph density:** does a denser G_LLM help downstream, or just add hallucinated edges (links H1↔H2)?

### 3.6 Pre-registered GO/NO-GO gate (first thing executed)
Run the **CIM↔ElecBench entity-overlap pre-check** before any downstream experiment. Decision rule
(thresholds frozen, exact - no tildes): **GO** if **≥ 50** topology/protection items are alignable to the
public CGMES case *and* at least **20** of them fall in the S2 (reasoning) stratum; **RESTRICT** to the
covered slice if **20-49** alignable items (report coverage as a limitation; H2 becomes a parity claim);
**DEMOTE to Idea 1** if **< 20**. These integers are backed by a pre-registered power analysis: at n=50
paired items with Holm correction across k=3 primary hypotheses, the minimum detectable per-metric effect is
**0.46 SD = ~23 pp (full set) / 0.65 SD = ~32 pp (S2 stratum, n=25)** at α=0.05, power=0.80. The overlap
number is reported regardless of outcome.

*Gate update (2026-06-10): Step -1 triggered - ElecBench corpus unavailable. H2 redesigned to custom
CIM-QA (50 items, S1=25, S2=25) derived from IEEE 14-bus CGMES case. MDE computed at these sample sizes
(registered above). See `GATE_REPORT.md` for full decision trace.*

## 4. Experiment Plan (pre-registered analyses & decision rules)

| Step | Action | Decision rule / output |
|------|--------|------------------------|
| **-1** | **PRECONDITION (executed 2026-06-10 - NO-GO).** Confirmed: ElecBench public release = 288 QA pairs, no source corpus, zero CIM-topology-answerable items. See `GATE_REPORT.md`. | **H2 pivot activated.** Downstream evaluation redesigned to use custom CIM-QA (50 items from CGMES case). Loss of ElecBench comparability stated as limitation. |
| 0 | **Stage data.** Clone ElecBench; source a public CGMES/IEC 61970 case (e.g., IEEE 14-/39-bus CGMES) + IEC 61850 reference. | Blocks everything downstream. |
| 1 | **Gate (§3.6).** Quantify CIM↔ElecBench overlap. | GO / RESTRICT / DEMOTE per frozen thresholds. |
| 2 | **Build G_STD and G_LLM**; log build cost (H3). | Cost table. |
| 3 | **Edge precision/recall vs schema** (H1) with alignment + IAA. | Primary objective result; the headline number. |
| 4 | **Downstream ElecBench** (H2): both pipelines, 6 metrics, ≥2 judges + human, paired tests, stratified. | Match-or-beat verdict on factuality/security. |
| 5 | **Ablations** (§3.5). | Density and edge-label effects. |
| 6 | **Judge-reliability harness** alongside Step 4. | Noise floor; gates interpretation of H2. |

**Minimum first pilot:** Step 1 (the gate) on one public CGMES case - cheap, decides go/no-go before any GPU spend.

**Pre-registered analyses (frozen):** edge precision/recall (endpoint vs type split); paired per-item CIM-QA
deltas with multiple-contrast control across the 3 primary contrasts (H1, H2-S1, H2-S2); build-cost ratio
G_LLM:G_STD; IAA for entity alignment; judge test-retest stability. We commit to reporting H1/H3 (objective)
**even if H2 (downstream) is null or judge-confounded.**

**MDE at registered sample size (GAP_GATE_MDE - now filled):**
Paired Wilcoxon, Holm correction across k=3 primary hypotheses, α=0.05, power=0.80:
- n=50 (full CIM-QA set): MDE ≈ **0.46 SD = ~23 percentage points** (binary accuracy at 50% baseline)
- n=25 (S2 stratum): MDE ≈ **0.65 SD = ~32 percentage points**
A standards-native graph with correct CIM topology is expected to dominate on S1 lookup items by >50 pp;
the S2 stratum MDE of 32 pp is the binding constraint. If the observed G_STD vs G_LLM S2 gap is ≥32 pp,
H2 reaches significance; smaller effects are underpowered and reported as inconclusive.

## 5. Threats to Validity & Mitigations

| Threat | Mitigation (pre-committed) |
|--------|----------------------------|
| **Partial CIM coverage** → edge-precision measured on a non-representative slice (the reviewer's top objection). | The §3.6 gate + always reporting coverage; RESTRICT mode confines claims to the covered slice. |
| **Entity-alignment subjectivity.** | Deterministic resolver + double annotation + reported IAA; scored only over aligned set. |
| **ElecBench factuality circularity.** ElecBench's factuality metric is itself defined as alignment with power-system standards, and G_STD is built from those same standards - a whiff of circularity in H2's factuality dimension. | *Moot after Step -1 pivot.* H2 now uses custom CIM-QA; factuality circularity does not apply. Named as limitation of original design. |
| **ElecBench dispatch-centric / topology-protection slice thin.** The benchmark's center of gravity is dispatch; topology/protection items may not reach ≥50/≥20-S2. | *Confirmed by gate (2026-06-10).* ElecBench public data has no topology items at all. Step -1 gate triggered; custom CIM-QA replaces ElecBench for H2. |
| **No retrievable ElecBench corpus** (only QA pairs). | **Confirmed.** Step -1 gate executed; NO-GO decision; pivot to custom CIM-QA per pre-registered fallback. |
| **G_STD vs G_LLM not the only difference.** | Identical retriever + reader; only graph source varies; ablate density/labels to localize cause. |
| **Single reader / single case** → external validity. | Frame as a focused controlled study; note generalization as future work; add a second CGMES case if budget allows. |
| **Same-family review** (no Codex/OpenAI). | Stated in the honesty banner; re-run Phase-4 quality review with a non-Claude reviewer before submission. |

## 6. Results & Discussion (placeholders: no experiments run)

<!-- DATA_NEEDED: GAP_S6_EDGE - H1 edge precision/recall table (endpoint vs type errors), with coverage -->
<!-- DATA_NEEDED: GAP_S6_DOWNSTREAM - H2 ElecBench 6-metric paired contrast, stratified, with judge agreement -->
<!-- DATA_NEEDED: GAP_S6_COST - H3 build-cost table (tokens/calls/wall-clock) G_LLM vs G_STD -->
<!-- DATA_NEEDED: GAP_S6_ABLATION - density and edge-label sensitivity studys -->
<!-- DATA_NEEDED: GAP_S6_DISCUSSION - interpretation: does the result indict or validate LLM graph extraction for safety-critical power use? -->

## References (anchored, verified: to expand in references.bib)

1. Zhou et al. *ElecBench: a Power Dispatch Evaluation Benchmark for LLMs.* arXiv:2407.05365, 2024.
2. *HG-RAG: Hierarchical Graph-Enhanced RAG for Power Systems.* Electronics (MDPI) 15(7):1445, 2026. doi:10.3390/electronics15071445.
3. Shi et al. *GridCodex: A RAG-Driven AI Framework for Power Grid Code Reasoning and Compliance.* arXiv:2508.12682, 2025.
4. Tang et al. *An Intelligent Question Answering System based on Power Knowledge Graph.* 2021.
5. Edge et al. *From Local to Global: A Graph RAG Approach to Query-Focused Summarization.* arXiv:2404.16130, 2024.
6. Xiang et al. *When to use Graphs in RAG: A Comprehensive Analysis (GraphRAG-Bench).* 2025-26 (arXiv:2506.05690).
7. Fan et al. *Do We Still Need GraphRAG? Benchmarking RAG and GraphRAG for Agentic Search.* 2026 (arXiv:2604.09666).
8. Guo et al. *LightRAG: Simple and Fast Retrieval-Augmented Generation.* arXiv:2410.05779, 2024.
9. Gutiérrez et al. *HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs.* arXiv:2405.14831, 2024.
10. Chen et al. *Are Large Language Models Effective Knowledge Graph Constructors?* arXiv:2510.11297, 2025.
11. Ma et al. *Toward Robust GraphRAG: Mitigating Retrieval Drift and Hallucination from Imperfect KGs.* arXiv:2603.14828, 2026.
12. *Document GraphRAG: KG-Enhanced RAG for Document QA in the Manufacturing Domain.* MDPI Electronics, 2025. doi:10.3390/electronics14112102.
13. Ahmad et al. *Benchmarking Vector, Graph and Hybrid RAG Pipelines for O-RAN.* 2025.

*(Full bibliographic detail and additional entries from `research-wiki/` to be compiled into `references.bib`.)*
