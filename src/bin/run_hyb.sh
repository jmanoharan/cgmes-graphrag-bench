#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
set -e
cd "$(dirname "$0")/../.."
echo "=== G_HYB MicroGrid ==="
V2_DATA=data/networks/microgrid python3 -m src.scoring.h2_eval --kg hyb --out-suffix _hyb
echo "=== G_HYB SmallGrid ==="
V2_DATA=data/networks/smallgrid python3 -m src.scoring.h2_eval --kg hyb --out-suffix _hyb
echo "G_HYB RUNS COMPLETE"
