# Results Files

Each JSON file here is a top-level summary of a specific experimental hypothesis.
The `data/networks/*/` directories contain per-item detail.

| File | Description | Paper location |
|------|-------------|----------------|
| `h1_microgrid.json` | H1 edge classification: G_LLM edge error rate, topological recall, entity alignment - MicroGrid | §VI-A, Table II |
| `h1_smallgrid.json` | H1 edge classification - SmallGrid | §VI-A, Table II |
| `h2_microgrid.json` | H2 QA accuracy by arm (std/llm/hyb), overall + S1/S2 - MicroGrid | §VI-B, Table I |
| `h2_smallgrid.json` | H2 QA accuracy - SmallGrid | §VI-B, Table I |
| `h3_costs.json` | Build cost contrast: G_STD (0 tokens) vs G_LLM (exact token accounting), both networks | §VI-C, Table III |
| `stats_microgrid.json` | Full statistical analysis: McNemar, Holm correction, CI, judge reliability κ - MicroGrid | §VI-B, §V |
| `stats_smallgrid.json` | Full statistical analysis - SmallGrid | §VI-B, §V |

## Key numbers (verified)

### H1: MicroGrid
- Edge error rate: **1.35%** (2/148 scored edges; TYPE_A+C)
- Topological recall: **53.4%** (159/298 pairs)
- Entity alignment: **80.5%** (120/149 entities)

### H2: MicroGrid (overall QA accuracy)
- G_STD: **82%** | G_LLM: **82%** | Δ = 0 pp | 95% CI [−13.6, +13.6] pp | McNemar p = 1.0

### H2: SmallGrid (overall QA accuracy)
- G_STD: **48%** | G_LLM: **98%** | Δ = −50 pp (G_LLM > G_STD)

### H3: Build cost (MicroGrid)
- G_STD: 0 tokens, 0 LLM calls, 9.8 ms
- G_LLM: 87,962 tokens, 18 calls, 78.2 s

### H3: Build cost (SmallGrid)
- G_STD: 0 tokens, 0 LLM calls
- G_LLM: 594,617 tokens, 112 calls, 643.7 s
