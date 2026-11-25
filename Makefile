.PHONY: all analysis figures excel manifest test clean
all: analysis figures excel manifest test
analysis: ; python scripts/02_run_analysis.py
figures:  ; python scripts/03_make_figures.py
excel:    ; python scripts/04_build_excel.py
manifest: ; python scripts/05_build_manifest.py
test:     ; pytest -q
clean:    ; rm -rf figures/generated/* results/*.csv data/processed/*.csv
