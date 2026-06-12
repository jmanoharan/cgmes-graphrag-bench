# Data Dictionary

This dictionary is generated from the released JSON artifacts and records the observed fields reviewers will encounter.

## Result summaries

### `results/h1_microgrid.json`

- JSON type: `dict`; entries/keys: `14`.
- Top-level/record fields: `aligned_entities`, `alignment_report`, `edge_classes`, `entity_alignment_rate`, `h1_denominator_aligned_scored`, `h1_error_rate`, `h1_match_rate`, `label_fidelity_among_matches`, `notes`, `recall_recovered_pairs`, `recall_universe_pairs`, `topological_recall`, `total_llm_edges`, `total_llm_entities`.
- `edge_classes` fields: `MATCH`, `TYPE_A`, `TYPE_B`, `TYPE_C`, `UNALIGNED`.

### `results/h1_smallgrid.json`

- JSON type: `dict`; entries/keys: `14`.
- Top-level/record fields: `aligned_entities`, `alignment_report`, `edge_classes`, `entity_alignment_rate`, `h1_denominator_aligned_scored`, `h1_error_rate`, `h1_match_rate`, `label_fidelity_among_matches`, `notes`, `recall_recovered_pairs`, `recall_universe_pairs`, `topological_recall`, `total_llm_edges`, `total_llm_entities`.
- `edge_classes` fields: `MATCH`, `TYPE_A`, `TYPE_B`, `TYPE_C`, `UNALIGNED`.

### `results/h2_microgrid.json`

- JSON type: `list`; entries/keys: `2`.
- Top-level/record fields: `claude_haiku_acc_all`, `det_acc_all`, `det_acc_s1`, `det_acc_s2`, `gpt51_acc_all`, `kg`, `n`.

### `results/h2_smallgrid.json`

- JSON type: `list`; entries/keys: `2`.
- Top-level/record fields: `claude_haiku_acc_all`, `det_acc_all`, `det_acc_s1`, `det_acc_s2`, `gpt51_acc_all`, `kg`, `n`.

### `results/h3_costs.json`

- JSON type: `dict`; entries/keys: `2`.
- Top-level/record fields: `microgrid`, `smallgrid`.
- `microgrid` fields: `g_llm`, `g_std`.
- `smallgrid` fields: `g_llm`, `g_std`.

### `results/stats_microgrid.json`

- JSON type: `dict`; entries/keys: `4`.
- Top-level/record fields: `h2_contrasts`, `h3`, `judge_reliability`, `registered_mde_note`.
- `h2_contrasts` fields: `All`, `S1`, `S2`.
- `judge_reliability` fields: `judge_errors`, `kappa_det_vs_claude`, `kappa_det_vs_gpt51`, `kappa_gpt51_vs_claude`.
- `h3` fields: `g_llm`, `g_std`, `note`, `token_gap`, `wall_ratio_llm_over_std`.

### `results/stats_smallgrid.json`

- JSON type: `dict`; entries/keys: `4`.
- Top-level/record fields: `h2_contrasts`, `h3`, `judge_reliability`, `registered_mde_note`.
- `h2_contrasts` fields: `All`, `S1`, `S2`.
- `judge_reliability` fields: `judge_errors`, `kappa_det_vs_claude`, `kappa_det_vs_gpt51`, `kappa_gpt51_vs_claude`.
- `h3` fields: `g_llm`, `g_std`, `note`, `token_gap`, `wall_ratio_llm_over_std`.

## Network-level JSON artifacts

### `data/networks/microgrid/cim_qa_items.json`

- JSON type: `list`; entries/keys: `50`.
- Top-level/record fields: `answer_spec`, `evidence`, `gold_answer`, `hop_count`, `id`, `question`, `stratum`.

### `data/networks/microgrid/corpus_facts.json`

- JSON type: `list`; entries/keys: `218`.
- Top-level/record fields: `a`, `b`, `rel`, `sentence`.

### `data/networks/microgrid/g_llm_edges.json`

- JSON type: `list`; entries/keys: `190`.
- Top-level/record fields: `description`, `dst`, `rel`, `src`, `weight`.

### `data/networks/microgrid/g_llm_entities.json`

- JSON type: `list`; entries/keys: `149`.
- Top-level/record fields: `description`, `id`, `type`.

### `data/networks/microgrid/g_std_edges.json`

- JSON type: `list`; entries/keys: `362`.
- Top-level/record fields: `dst`, `rel`, `src`.

### `data/networks/microgrid/g_std_nodes.json`

- JSON type: `list`; entries/keys: `233`.
- Top-level/record fields: `attrs`, `class`, `id`, `mrid`, `name`.

### `data/networks/microgrid/g_std_support.json`

- JSON type: `list`; entries/keys: `582`.
- Top-level/record fields: `a`, `b`, `rel`.

### `data/networks/microgrid/h1_edge_audit.json`

- JSON type: `list`; entries/keys: `190`.
- Top-level/record fields: `canonical_label`, `class`, `dst`, `label_compatible`, `rel`, `src`, `support`.

### `data/networks/microgrid/h1_results.json`

- JSON type: `dict`; entries/keys: `14`.
- Top-level/record fields: `aligned_entities`, `alignment_report`, `edge_classes`, `entity_alignment_rate`, `h1_denominator_aligned_scored`, `h1_error_rate`, `h1_match_rate`, `label_fidelity_among_matches`, `notes`, `recall_recovered_pairs`, `recall_universe_pairs`, `topological_recall`, `total_llm_edges`, `total_llm_entities`.
- `edge_classes` fields: `MATCH`, `TYPE_A`, `TYPE_B`, `TYPE_C`, `UNALIGNED`.

### `data/networks/microgrid/h2_results.json`

- JSON type: `list`; entries/keys: `100`.
- Top-level/record fields: `context_chars`, `det_verdict`, `gold`, `id`, `judge_claude_haiku`, `judge_gpt51`, `kg`, `latency_s`, `n_seeds`, `predicted`, `question`, `seed_fallback`, `stratum`.

### `data/networks/microgrid/h2_results_hop3_s2.json`

- JSON type: `list`; entries/keys: `50`.
- Top-level/record fields: `context_chars`, `det_verdict`, `gold`, `id`, `kg`, `latency_s`, `n_seeds`, `predicted`, `question`, `seed_fallback`, `stratum`.

### `data/networks/microgrid/h2_results_hyb.json`

- JSON type: `list`; entries/keys: `50`.
- Top-level/record fields: `context_chars`, `det_verdict`, `gold`, `id`, `judge_claude_haiku`, `judge_gpt51`, `kg`, `latency_s`, `n_seeds`, `predicted`, `question`, `seed_fallback`, `stratum`.

### `data/networks/microgrid/h2_summary.json`

- JSON type: `list`; entries/keys: `2`.
- Top-level/record fields: `claude_haiku_acc_all`, `det_acc_all`, `det_acc_s1`, `det_acc_s2`, `gpt51_acc_all`, `kg`, `n`.

### `data/networks/microgrid/h2_summary_hop3_s2.json`

- JSON type: `list`; entries/keys: `2`.
- Top-level/record fields: `det_acc_all`, `det_acc_s1`, `det_acc_s2`, `kg`, `n`.

### `data/networks/microgrid/h2_summary_hyb.json`

- JSON type: `list`; entries/keys: `1`.
- Top-level/record fields: `claude_haiku_acc_all`, `det_acc_all`, `det_acc_s1`, `det_acc_s2`, `gpt51_acc_all`, `kg`, `n`.

### `data/networks/microgrid/h3_g_llm_cost.json`

- JSON type: `dict`; entries/keys: `9`.
- Top-level/record fields: `completion_tokens`, `corpus_words`, `edges`, `llm_calls`, `method`, `nodes`, `prompt_tokens`, `total_tokens`, `wall_sec`.

### `data/networks/microgrid/h3_g_std_cost.json`

- JSON type: `dict`; entries/keys: `7`.
- Top-level/record fields: `edges`, `llm_calls`, `llm_tokens`, `method`, `nodes`, `source`, `wall_sec`.

### `data/networks/microgrid/stats_v2.json`

- JSON type: `dict`; entries/keys: `4`.
- Top-level/record fields: `h2_contrasts`, `h3`, `judge_reliability`, `registered_mde_note`.
- `h2_contrasts` fields: `All`, `S1`, `S2`.
- `judge_reliability` fields: `judge_errors`, `kappa_det_vs_claude`, `kappa_det_vs_gpt51`, `kappa_gpt51_vs_claude`.
- `h3` fields: `g_llm`, `g_std`, `note`, `token_gap`, `wall_ratio_llm_over_std`.

### `data/networks/microgrid_var1/g_llm_edges.json`

- JSON type: `list`; entries/keys: `227`.
- Top-level/record fields: `description`, `dst`, `rel`, `src`, `weight`.

### `data/networks/microgrid_var1/g_llm_entities.json`

- JSON type: `list`; entries/keys: `171`.
- Top-level/record fields: `description`, `id`, `type`.

### `data/networks/microgrid_var1/g_std_edges.json`

- JSON type: `list`; entries/keys: `362`.
- Top-level/record fields: `dst`, `rel`, `src`.

### `data/networks/microgrid_var1/g_std_nodes.json`

- JSON type: `list`; entries/keys: `233`.
- Top-level/record fields: `attrs`, `class`, `id`, `mrid`, `name`.

### `data/networks/microgrid_var1/g_std_support.json`

- JSON type: `list`; entries/keys: `582`.
- Top-level/record fields: `a`, `b`, `rel`.

### `data/networks/microgrid_var1/h1_edge_audit.json`

- JSON type: `list`; entries/keys: `227`.
- Top-level/record fields: `canonical_label`, `class`, `dst`, `label_compatible`, `rel`, `src`, `support`.

### `data/networks/microgrid_var1/h1_results.json`

- JSON type: `dict`; entries/keys: `14`.
- Top-level/record fields: `aligned_entities`, `alignment_report`, `edge_classes`, `entity_alignment_rate`, `h1_denominator_aligned_scored`, `h1_error_rate`, `h1_match_rate`, `label_fidelity_among_matches`, `notes`, `recall_recovered_pairs`, `recall_universe_pairs`, `topological_recall`, `total_llm_edges`, `total_llm_entities`.
- `edge_classes` fields: `MATCH`, `TYPE_A`, `TYPE_B`, `TYPE_C`, `UNALIGNED`.

### `data/networks/microgrid_var1/h3_g_llm_cost.json`

- JSON type: `dict`; entries/keys: `9`.
- Top-level/record fields: `completion_tokens`, `corpus_words`, `edges`, `llm_calls`, `method`, `nodes`, `prompt_tokens`, `total_tokens`, `wall_sec`.

### `data/networks/microgrid_var2/g_llm_edges.json`

- JSON type: `list`; entries/keys: `242`.
- Top-level/record fields: `description`, `dst`, `rel`, `src`, `weight`.

### `data/networks/microgrid_var2/g_llm_entities.json`

- JSON type: `list`; entries/keys: `166`.
- Top-level/record fields: `description`, `id`, `type`.

### `data/networks/microgrid_var2/g_std_edges.json`

- JSON type: `list`; entries/keys: `362`.
- Top-level/record fields: `dst`, `rel`, `src`.

### `data/networks/microgrid_var2/g_std_nodes.json`

- JSON type: `list`; entries/keys: `233`.
- Top-level/record fields: `attrs`, `class`, `id`, `mrid`, `name`.

### `data/networks/microgrid_var2/g_std_support.json`

- JSON type: `list`; entries/keys: `582`.
- Top-level/record fields: `a`, `b`, `rel`.

### `data/networks/microgrid_var2/h1_edge_audit.json`

- JSON type: `list`; entries/keys: `242`.
- Top-level/record fields: `canonical_label`, `class`, `dst`, `label_compatible`, `rel`, `src`, `support`.

### `data/networks/microgrid_var2/h1_results.json`

- JSON type: `dict`; entries/keys: `14`.
- Top-level/record fields: `aligned_entities`, `alignment_report`, `edge_classes`, `entity_alignment_rate`, `h1_denominator_aligned_scored`, `h1_error_rate`, `h1_match_rate`, `label_fidelity_among_matches`, `notes`, `recall_recovered_pairs`, `recall_universe_pairs`, `topological_recall`, `total_llm_edges`, `total_llm_entities`.
- `edge_classes` fields: `MATCH`, `TYPE_A`, `TYPE_B`, `TYPE_C`, `UNALIGNED`.

### `data/networks/microgrid_var2/h3_g_llm_cost.json`

- JSON type: `dict`; entries/keys: `9`.
- Top-level/record fields: `completion_tokens`, `corpus_words`, `edges`, `llm_calls`, `method`, `nodes`, `prompt_tokens`, `total_tokens`, `wall_sec`.

### `data/networks/smallgrid/cim_qa_items.json`

- JSON type: `list`; entries/keys: `50`.
- Top-level/record fields: `answer_spec`, `evidence`, `gold_answer`, `hop_count`, `id`, `question`, `stratum`.

### `data/networks/smallgrid/corpus_facts.json`

- JSON type: `list`; entries/keys: `1507`.
- Top-level/record fields: `a`, `b`, `rel`, `sentence`.

### `data/networks/smallgrid/g_llm_edges.json`

- JSON type: `list`; entries/keys: `1544`.
- Top-level/record fields: `description`, `dst`, `rel`, `src`, `weight`.

### `data/networks/smallgrid/g_llm_entities.json`

- JSON type: `list`; entries/keys: `1179`.
- Top-level/record fields: `description`, `id`, `type`.

### `data/networks/smallgrid/g_std_edges.json`

- JSON type: `list`; entries/keys: `2184`.
- Top-level/record fields: `dst`, `rel`, `src`.

### `data/networks/smallgrid/g_std_nodes.json`

- JSON type: `list`; entries/keys: `1398`.
- Top-level/record fields: `attrs`, `class`, `id`, `mrid`, `name`.

### `data/networks/smallgrid/g_std_support.json`

- JSON type: `list`; entries/keys: `3846`.
- Top-level/record fields: `a`, `b`, `rel`.

### `data/networks/smallgrid/h1_edge_audit.json`

- JSON type: `list`; entries/keys: `1544`.
- Top-level/record fields: `canonical_label`, `class`, `dst`, `label_compatible`, `rel`, `src`, `support`.

### `data/networks/smallgrid/h1_results.json`

- JSON type: `dict`; entries/keys: `14`.
- Top-level/record fields: `aligned_entities`, `alignment_report`, `edge_classes`, `entity_alignment_rate`, `h1_denominator_aligned_scored`, `h1_error_rate`, `h1_match_rate`, `label_fidelity_among_matches`, `notes`, `recall_recovered_pairs`, `recall_universe_pairs`, `topological_recall`, `total_llm_edges`, `total_llm_entities`.
- `edge_classes` fields: `MATCH`, `TYPE_A`, `TYPE_B`, `TYPE_C`, `UNALIGNED`.

### `data/networks/smallgrid/h2_results.json`

- JSON type: `list`; entries/keys: `100`.
- Top-level/record fields: `context_chars`, `det_verdict`, `gold`, `id`, `judge_claude_haiku`, `judge_gpt51`, `kg`, `latency_s`, `n_seeds`, `predicted`, `question`, `seed_fallback`, `stratum`.

### `data/networks/smallgrid/h2_results_hyb.json`

- JSON type: `list`; entries/keys: `50`.
- Top-level/record fields: `context_chars`, `det_verdict`, `gold`, `id`, `judge_claude_haiku`, `judge_gpt51`, `kg`, `latency_s`, `n_seeds`, `predicted`, `question`, `seed_fallback`, `stratum`.

### `data/networks/smallgrid/h2_summary.json`

- JSON type: `list`; entries/keys: `2`.
- Top-level/record fields: `claude_haiku_acc_all`, `det_acc_all`, `det_acc_s1`, `det_acc_s2`, `gpt51_acc_all`, `kg`, `n`.

### `data/networks/smallgrid/h2_summary_hyb.json`

- JSON type: `list`; entries/keys: `1`.
- Top-level/record fields: `claude_haiku_acc_all`, `det_acc_all`, `det_acc_s1`, `det_acc_s2`, `gpt51_acc_all`, `kg`, `n`.

### `data/networks/smallgrid/h3_g_llm_cost.json`

- JSON type: `dict`; entries/keys: `9`.
- Top-level/record fields: `completion_tokens`, `corpus_words`, `edges`, `llm_calls`, `method`, `nodes`, `prompt_tokens`, `total_tokens`, `wall_sec`.

### `data/networks/smallgrid/h3_g_std_cost.json`

- JSON type: `dict`; entries/keys: `7`.
- Top-level/record fields: `edges`, `llm_calls`, `llm_tokens`, `method`, `nodes`, `source`, `wall_sec`.

### `data/networks/smallgrid/stats_v2.json`

- JSON type: `dict`; entries/keys: `4`.
- Top-level/record fields: `h2_contrasts`, `h3`, `judge_reliability`, `registered_mde_note`.
- `h2_contrasts` fields: `All`, `S1`, `S2`.
- `judge_reliability` fields: `judge_errors`, `kappa_det_vs_claude`, `kappa_det_vs_gpt51`, `kappa_gpt51_vs_claude`.
- `h3` fields: `g_llm`, `g_std`, `note`, `token_gap`, `wall_ratio_llm_over_std`.

## Common field meanings

- `id`, `src`, `dst`, `rel`: graph identifiers and directed relation triples.
- `class`, `type`, `name`, `attrs`, `description`: CIM or extracted entity metadata.
- `kg`: graph arm (`std`, `llm`, or `hyb`).
- `det_acc_all`, `det_acc_s1`, `det_acc_s2`: deterministic QA accuracy overall and by stratum.
- `total_tokens`, `prompt_tokens`, `completion_tokens`, `calls`, `wall_s`: exact LLM-build accounting.
- `h1_error_rate`, `topological_recall`, `entity_alignment`: H1 extraction-fidelity metrics.
- `answer_spec`, `expected`, `pred`, `correct`: QA gold specification and scoring outputs.
