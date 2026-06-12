# Data Layout

## cgmes/

Raw CGMES v2.4.15 XML files from the ENTSO-E Conformity Assessment test configurations:

- `MicroGrid_BC_Assembled/` - MicroGrid BaseCase (BE+NL boundary assembled): 233 CIM objects,
  9 association types used for G_STD, 362 edges.
- `SmallGrid_BC/` - SmallGrid BaseCase: 1,398 CIM objects, 2,184 edges.

**Source:** ENTSO-E CGMES Conformity Assessment configurations, mirrored in the powsybl/powsybl-core
repository (`cgmes-conformity` resources, `cas-1.1.3-data-4.0.3`). These files are provided under
ENTSO-E attribution terms; see `paper/supplementary/DEVIATIONS.md` §C for provenance. Data files in this
repository are released under CC-BY-4.0 where redistribution is permitted; see `LICENSE-DATA`.

## networks/

Pre-built graph artefacts, corpus, QA items, and scoring results for each experimental case.

| Directory | Description |
|-----------|-------------|
| `microgrid/` | MicroGrid BC - primary case (v2, final) |
| `microgrid_var1/` | MicroGrid variant build 1 (H1 variability estimate) |
| `microgrid_var2/` | MicroGrid variant build 2 (H1 variability estimate) |
| `smallgrid/` | SmallGrid BC - second case (D1 post-hoc addition) |

### Key files in each network directory

| File | Description |
|------|-------------|
| `g_std_nodes.json` | G_STD nodes (CIM objects) |
| `g_std_edges.json` | G_STD edges (real CIM association edges) |
| `g_std_support.json` | G_STD derived semantic support relations |
| `g_llm_entities.json` | G_LLM entities extracted by LightRAG |
| `g_llm_edges.json` | G_LLM edges extracted by LightRAG |
| `corpus.txt` | Deterministic NL rendering of the CGMES model |
| `corpus_facts.json` | Corpus-expressible fact registry (Type-B oracle) |
| `cim_qa_items.json` | 50 QA items with machine-checkable answer_spec |
| `h1_results.json` | H1 edge classification summary |
| `h1_edge_audit.json` | Per-edge H1 audit trail |
| `h2_results.json` | Per-item H2 QA results (G_STD arm) |
| `h2_summary.json` | H2 summary by KG arm |
| `h3_g_std_cost.json` | G_STD build cost (0 tokens) |
| `h3_g_llm_cost.json` | G_LLM build cost (exact token accounting) |
| `stats_v2.json` | Full statistical results (H2 + H3 + judge reliability) |
| `lightrag_workdir/` | Pre-built LightRAG state (graph + KV cache). Reviewers who want to reproduce scoring/eval without rebuilding G_LLM can use this cached workdir directly. |
