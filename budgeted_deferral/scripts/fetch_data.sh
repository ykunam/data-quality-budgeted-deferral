#!/usr/bin/env bash
# Fetch the four public datasets into budgeted_deferral/data/.
# Source: a public mirror of the original UCI files and the HMEQ data set
# (https://github.com/JLZml/Credit-Scoring-Data-Sets). Originals: UCI ML Repository
# (German C5NC77, Australian C59012, Default C55S3H) and Baesens et al. (2016) for HMEQ.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
git clone --depth 1 https://github.com/JLZml/Credit-Scoring-Data-Sets "$tmp/cs"
cp "$tmp/cs/1. UCI Repository/German/german.data-numeric" data/
cp "$tmp/cs/1. UCI Repository/Australian/australian.dat" data/
cp "$tmp/cs/6. Credit risk analysis/hmeq/hmeq.csv" data/
cp "$tmp/cs/1. UCI Repository/Taiwan/default of credit card clients.xls" data/default.xls
# convert xls -> csv (LibreOffice; alternatively: pandas.read_excel with xlrd installed)
if command -v soffice >/dev/null; then
  (cd data && soffice --headless --convert-to csv default.xls >/dev/null)
else
  python - <<'PY'
import pandas as pd
pd.read_excel("data/default.xls", header=None).to_csv("data/default.csv", index=False, header=False)
PY
fi
rm -rf "$tmp"
sha256sum data/german.data-numeric data/australian.dat data/hmeq.csv data/default.csv
