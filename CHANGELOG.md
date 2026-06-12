# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-06-12

### Changed
- Added Zenodo concept DOI (10.5281/zenodo.20671115) to citation metadata and README.

## [1.0.0] - 2026-06-11

### Added
- Initial public release accompanying the paper submission.
- `src/cgmes_parse/`: CGMES RDF/XML parser producing G_STD.
- `src/lightrag_extract/`: LightRAG-based G_LLM builder with exact token accounting.
- `src/scoring/`: H1 edge classifier, H2 QA evaluator, and statistical analysis.
- `data/cgmes/`: ENTSO-E CGMES Conformity Assessment test configurations (MicroGrid, SmallGrid).
- `data/networks/`: Pre-built graph artefacts and LightRAG KV caches for both networks.
- `results/`: Final numerical results backing all paper claims.
- `paper/`: Conference version PDF.
- `paper/supplementary/`: Pre-registration, deviations register, human spot-check sheet.

### Notes
- The v1 run (2026-06-10) contained several protocol violations (use of pandapower
  IEEE-14 case with invented relation labels instead of a real CGMES export, unregistered
  strong reader model, single judge). All violations are documented in
  `paper/supplementary/DEVIATIONS.md`. The v1 artefacts are not released; results from
  v1 must not be cited.
