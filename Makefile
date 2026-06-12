# SPDX-License-Identifier: Apache-2.0
.PHONY: setup build-g-std build-g-llm eval-h1 eval-h2 stats all clean

PYTHON ?= python3

setup:
	pip install -r requirements.txt

build-g-std:
	V2_DATA=data/networks/microgrid $(PYTHON) -m src.cgmes_parse.build_g_std
	V2_DATA=data/networks/smallgrid $(PYTHON) -m src.cgmes_parse.build_g_std --case smallgrid

build-g-llm:
	@echo "NOTE: G_LLM build requires AZURE_OPENAI_API_KEY (or compatible LLM endpoint)."
	@echo "      If you want to skip this step, pre-built caches are in data/networks/*/lightrag_workdir/."
	V2_DATA=data/networks/microgrid $(PYTHON) -m src.lightrag_extract.build_g_llm
	V2_DATA=data/networks/smallgrid $(PYTHON) -m src.lightrag_extract.build_g_llm

eval-h1:
	V2_DATA=data/networks/microgrid $(PYTHON) -m src.scoring.h1_edge_classifier
	V2_DATA=data/networks/smallgrid $(PYTHON) -m src.scoring.h1_edge_classifier

eval-h2:
	V2_DATA=data/networks/microgrid $(PYTHON) -m src.scoring.h2_eval --kg std
	V2_DATA=data/networks/microgrid $(PYTHON) -m src.scoring.h2_eval --kg llm
	V2_DATA=data/networks/microgrid $(PYTHON) -m src.scoring.h2_eval --kg hyb
	V2_DATA=data/networks/smallgrid $(PYTHON) -m src.scoring.h2_eval --kg std
	V2_DATA=data/networks/smallgrid $(PYTHON) -m src.scoring.h2_eval --kg llm
	V2_DATA=data/networks/smallgrid $(PYTHON) -m src.scoring.h2_eval --kg hyb

stats:
	V2_DATA=data/networks/microgrid $(PYTHON) -m src.scoring.stats
	V2_DATA=data/networks/smallgrid $(PYTHON) -m src.scoring.stats

all: eval-h1 eval-h2 stats

clean:
	find . -name "__pycache__" -type d | xargs rm -rf 2>/dev/null || true
