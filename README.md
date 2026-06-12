# Trustworthy Knowledge Graphs for Grid Digitalization: Standards-Native CIM/CGMES vs. LLM-Extracted Graphs in Power-System GraphRAG

Official artifact repository (CGMES GraphRAG Bench) for the paper.

**Keywords:** CIM, CGMES, IEC 61970, GraphRAG, power systems, knowledge graph, retrieval-augmented generation, trustworthy AI, LLM reliability, grid digitalization

![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Data License](https://img.shields.io/badge/data-CC--BY--4.0-lightgrey)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20671115.svg)](https://doi.org/10.5281/zenodo.20671115)

## What this is

CGMES GraphRAG Bench is a reviewer-ready artifact for a controlled study of graph source effects in power-system retrieval-augmented generation. It packages the conference paper PDF, CGMES test models, graph-building scripts, scoring scripts, and final numerical results in one reproducible repository.

For power-systems researchers, the central question is practical: when the grid model is already available as standards-compliant CIM/CGMES, should a GraphRAG system parse that model directly or first ask an LLM extraction pipeline to induce a graph from text? This benchmark keeps the reader, retriever, QA items, and scoring fixed so that only the knowledge-graph source differs.

## Key results

| Arm | MicroGrid QA | SmallGrid QA | Build tokens |
|-----|-------------|-------------|-------------|
| G_STD (standards-native) | 82% | 48% | 0 |
| G_LLM (LightRAG) | 82% | 98% | 87,962 / 594,617 |
| G_HYB (hybrid, exploratory) | 74% | 54% | 0 |

## Reproduce in 5 commands

```bash
git clone https://github.com/jmanoharan/cgmes-graphrag-bench.git
cd cgmes-graphrag-bench
make setup
make eval-h1 eval-h2 stats
```

Optional: `make build-g-llm` rebuilds the LightRAG graph and requires an OpenAI-compatible API endpoint; cached LightRAG artifacts are included for review.

## Repository layout

```text
cgmes-graphrag-bench/
├── paper/                  # Conference PDF and supplementary materials
│   ├── paper_conference.pdf
│   └── supplementary/
├── src/                    # CGMES parser, LightRAG builder, scoring scripts
│   ├── cgmes_parse/
│   ├── lightrag_extract/
│   ├── scoring/
│   └── bin/
├── data/                   # Raw CGMES models and derived network artifacts
│   ├── cgmes/
│   └── networks/
├── results/                # Top-level JSON result summaries
└── docs/                   # Reproduction guide, methodology note, data dictionary
```

## How to cite

```bibtex
@inproceedings{manoharan2026cgmesgraphragbench,
  title={Trustworthy Knowledge Graphs for Grid Digitalization: Standards-Native CIM/CGMES vs. LLM-Extracted Graphs in Power-System GraphRAG},
  author={Manoharan, Jayakumar},
  booktitle={submitted},
  year={2026}
}
```

## Paper links

- Conference PDF: [`paper/paper_conference.pdf`](paper/paper_conference.pdf)
- Supplementary files: [`paper/supplementary/`](paper/supplementary/)

## License + contact

Code is released under Apache-2.0; see [`LICENSE`](LICENSE). Data and documentation are released under CC-BY-4.0 where redistribution is permitted; see [`LICENSE-DATA`](LICENSE-DATA) and [`data/README.md`](data/README.md) for provenance notes.

Contact: Jayakumar Manoharan, Electric Power Research Institute (EPRI), jmanoharan@epri.com.

## Acknowledgements

The benchmark uses CGMES conformity models from ENTSO-E and the IEC Common Information Model / CGMES standards ecosystem. The authors thank the maintainers of LightRAG, NetworkX, lxml, sentence-transformers, and the open scientific Python stack.
