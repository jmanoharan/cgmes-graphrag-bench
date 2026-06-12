# Methodology Note

This note provides a condensed, self-contained description of the experimental
methodology, mirroring §IV of the paper but readable without the LaTeX source.

## 1. Research question

Does the source of the knowledge graph - standards-native (parsed from CGMES) vs
LLM-extracted (LightRAG over a deterministic corpus) - affect downstream QA accuracy
inside an otherwise frozen GraphRAG pipeline on CIM/CGMES power-system networks?

## 2. Experimental design

The study uses a **controlled, pre-registered, paired contrast**.
Only the graph source differs between arms; the retrieval, reader, and scoring are
identical for all arms.

- **G_STD**: Built by deterministic RDF/XML parse of the CGMES export.
  Zero LLM calls. Nodes = CIM objects (mRID, class, name, attributes).
  Edges = real CIM association triples (`Terminal.ConductingEquipment`, etc.).
  Derived semantic support relations are added to expose implicit topology.

- **G_LLM**: Built by LightRAG 1.5.1 over a deterministic NL corpus
  (template rendering of the CGMES model; no LLM in corpus generation).
  Builder: Azure OpenAI `gpt-5.1`. Embeddings: `all-MiniLM-L6-v2` (local).

- **G_HYB**: Post-hoc exploratory arm. G_STD compressed with five derived
  support relation types; zero LLM cost. Added after the SmallGrid scale
  mechanism was diagnosed (§VI-D of the paper); labeled non-registered.

## 3. Networks

Two ENTSO-E CGMES Conformity Assessment test configurations:

| Network | CIM objects | CIM edges | QA items |
|---------|-------------|-----------|----------|
| MicroGrid BC Assembled | 233 | 362 | 50 |
| SmallGrid BC | 1,398 | 2,184 | 50 |

## 4. QA design and scoring

50 QA items per network, stratified S1 (attribute lookup; numeric/string answer)
and S2 (structural/topological; requires multi-hop CIM traversal).
Gold answers carry machine-checkable `answer_spec` fields; primary scoring is
**deterministic** (string/numeric normalisation; no LLM judge for primary verdicts).
Secondary: two LLM judges from different families (Azure `gpt-5.1`, Claude Haiku),
serving as inter-rater reliability check. Pairwise κ(gpt-5.1, Claude Haiku) = 1.0;
κ(deterministic, LLM judges) = 0.97.

## 5. H1: extraction fidelity

Each G_LLM edge is classified:
- **MATCH**: endpoints co-occur in G_STD support (label fidelity reported separately).
- **TYPE_A**: unsupported, not corpus-expressed, relation maps to a schema-class name.
- **TYPE_B**: unsupported, corpus-expressed (excluded from precision denominator).
- **TYPE_C**: unsupported, not corpus-expressed, unmappable label.

H1 error rate = (TYPE_A + TYPE_C) / (aligned edges − TYPE_B).
Topological recall = fraction of G_STD support pairs recovered by any G_LLM edge.

## 6. H2: downstream QA

Retrieval: 2-hop subgraph expansion from question-entity seeds; uniform triple
rendering; 8,000-char context cap; identical for all arms.
Reader: Qwen2.5-7B-Instruct, local, greedy decoding.
Statistical test: McNemar exact (primary); Wilcoxon sign-test (confirmatory).
Holm correction across 3 registered contrasts (All, S1, S2).
Pre-registered MDE: ≈23 pp overall, ≈32 pp per stratum.

## 7. H3: build cost

Exact per-call accounting logged by the builder script. G_STD cost = 0 tokens
(parse only). Ratio G_LLM/G_STD = ∞ tokens; wall time ≈ 78 s vs 0.01 s (MicroGrid).

## 8. Key findings

- **MicroGrid**: G_STD and G_LLM reach identical downstream QA (82%/82%);
  null decomposes into opposite-signed stratum effects both below the MDE.
  LLM extraction is precise (1.35% schema error) but captures only 53.4% of topology.
  
- **SmallGrid**: Pattern reverses (G_LLM 98%, G_STD 48%); diagnosed mechanism is
  context truncation - 45/50 G_STD retrievals hit the 8,000-char cap, burying
  the answer. G_HYB at 0 tokens recovers partially (54%).
