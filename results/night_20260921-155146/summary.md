# NIGHT-1 summary

## Run overview

- models run: 24 (aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b)
- tests run: 25 (HOME-01, HOME-02, HOME-03, HOME-04, HOME-05, HOME-06, HOME-07, HOME-08, HOME-09, HOME-10, HOME-11, HOME-12, HOME-13, HOME-14, HOME-15, HOME-16, HOME-17, HOME-18, HOME-19, HOME-20, HOME-21, HOME-22, HOME-23, HOME-24, PERF)
- records: 4190
- wall time total (sum wall_s): 27179.2 s
- NOT_RUN_BUDGET: 799
- counts by status:
  - CONTEXT_OVERFLOW: 4
  - FORMAT_ERROR: 459
  - NOT_RUN_BUDGET: 799
  - OK: 1755
  - OUTPUT_TRUNCATED: 191
  - UNSUPPORTED_CAPABILITY: 406
  - WRONG_ANSWER: 576

## Per-test ranking (by Q_sem)
### HOME-01
- qwen3.5:4b: Q_sem=0.944 Q_strict=0.944 n=24/24 cases=24 coverage=1.000 CI=[0.910,0.972]
- llama3.1:8b: Q_sem=0.885 Q_strict=0.885 n=24/24 cases=24 coverage=1.000 CI=[0.851,0.920]
- aya-expanse:8b: Q_sem=0.858 Q_strict=0.858 n=24/24 cases=24 coverage=1.000 CI=[0.816,0.896]
- qwen3:1.7b: Q_sem=0.851 Q_strict=0.851 n=24/24 cases=24 coverage=1.000 CI=[0.809,0.892]
- lfm2.5:8b: Q_sem=0.833 Q_strict=0.833 n=24/24 cases=24 coverage=1.000 CI=[0.740,0.910]
- phi4-mini:latest: Q_sem=0.795 Q_strict=0.000 n=24/24 cases=24 coverage=1.000 CI=[0.736,0.851]
- qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=12/24 cases=24 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=0.986 Q_strict=0.000 n=12/24 cases=24 coverage=0.500 CI=[0.972,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.972 Q_strict=0.972 n=12/24 cases=24 coverage=0.500 CI=[0.931,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.924 Q_strict=0.924 n=12/24 cases=24 coverage=0.500 CI=[0.854,0.979] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.806 Q_strict=0.639 n=12/24 cases=24 coverage=0.500 CI=[0.569,0.986] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.778 Q_strict=0.639 n=12/24 cases=24 coverage=0.500 CI=[0.708,0.847] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_LOSS (best=aya-expanse:8b vs qwen3.5:4b, common_n=24)
### HOME-02
- bge-m3:latest: Q_sem=0.923 Q_strict=0.923 n=40/40 cases=40 coverage=1.000 CI=[0.888,0.957]
- UNSUPPORTED (not ranked): aya-expanse:8b, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-03
- lfm2.5:8b: Q_sem=0.938 Q_strict=0.938 n=16/16 cases=16 coverage=1.000 CI=[0.812,1.000]
- llama3.1:8b: Q_sem=0.938 Q_strict=0.938 n=16/16 cases=16 coverage=1.000 CI=[0.812,1.000]
- qwen3.5:4b: Q_sem=0.750 Q_strict=0.750 n=16/16 cases=16 coverage=1.000 CI=[0.500,0.938]
- qwen3:1.7b: Q_sem=0.688 Q_strict=0.688 n=16/16 cases=16 coverage=1.000 CI=[0.438,0.875]
- phi4-mini:latest: Q_sem=0.562 Q_strict=0.562 n=16/16 cases=16 coverage=1.000 CI=[0.312,0.812]
- command-r7b:7b: Q_sem=0.000 Q_strict=0.000 n=16/16 cases=16 coverage=1.000 CI=[0.000,0.000]
- deepseek-r1:8b: Q_sem=1.000 Q_strict=0.300 n=10/16 cases=16 coverage=0.625 CI=[1.000,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=1.000 Q_strict=0.000 n=10/16 cases=16 coverage=0.625 CI=[1.000,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.900 Q_strict=0.900 n=10/16 cases=16 coverage=0.625 CI=[0.700,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.900 Q_strict=0.900 n=10/16 cases=16 coverage=0.625 CI=[0.700,1.000] [insufficient coverage - not ranked]
- aya-expanse:8b: Q_sem=0.800 Q_strict=0.100 n=10/16 cases=16 coverage=0.625 CI=[0.600,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.800 Q_strict=0.800 n=10/16 cases=16 coverage=0.625 CI=[0.500,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_LOSS (best=command-r7b:7b vs lfm2.5:8b, common_n=16)
### HOME-04
- lfm2.5:8b: Q_sem=0.917 Q_strict=0.917 n=12/12 cases=12 coverage=1.000 CI=[0.750,1.000]
- qwen3:1.7b: Q_sem=0.833 Q_strict=0.833 n=12/12 cases=12 coverage=1.000 CI=[0.583,1.000]
- phi4-mini:latest: Q_sem=0.583 Q_strict=0.583 n=12/12 cases=12 coverage=1.000 CI=[0.333,0.833]
- deepseek-r1:8b: Q_sem=0.333 Q_strict=0.333 n=12/12 cases=12 coverage=1.000 CI=[0.083,0.583]
- qwen3.5:4b: Q_sem=0.167 Q_strict=0.167 n=12/12 cases=12 coverage=1.000 CI=[0.000,0.417]
- qwen3:8b: Q_sem=0.667 Q_strict=0.667 n=6/12 cases=12 coverage=0.500 CI=[0.333,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=0.500 Q_strict=0.500 n=6/12 cases=12 coverage=0.500 CI=[0.167,0.833] [insufficient coverage - not ranked]
- qwen2.5-coder:7b: Q_sem=0.167 Q_strict=0.167 n=6/12 cases=12 coverage=0.500 CI=[0.000,0.500] [insufficient coverage - not ranked]
- llama3.1:8b: Q_sem=0.000 Q_strict=0.000 n=6/12 cases=12 coverage=0.500 CI=[0.000,0.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.000 Q_strict=0.000 n=6/12 cases=12 coverage=0.500 CI=[0.000,0.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
- NOT_RUN_BUDGET (not ranked): qwen3:14b
  HOME verdict: HOME_LOSS (best=deepseek-r1:8b vs lfm2.5:8b, common_n=12)
### HOME-05
- qwen3.5:4b: Q_sem=0.500 Q_strict=0.250 n=12/12 cases=12 coverage=1.000 CI=[0.250,0.833]
- qwen2.5vl:7b: Q_sem=0.417 Q_strict=0.417 n=12/12 cases=12 coverage=1.000 CI=[0.167,0.667]
- gemma3:12b: Q_sem=0.333 Q_strict=0.167 n=12/12 cases=12 coverage=1.000 CI=[0.083,0.583]
- granite3.2-vision:2b: Q_sem=0.000 Q_strict=0.000 n=4/12 cases=12 coverage=0.333 CI=[0.000,0.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=gemma3:12b vs qwen3.5:4b, common_n=12)
### HOME-06
- phi4-mini:latest: Q_sem=1.000 Q_strict=0.750 n=12/12 cases=12 coverage=1.000 CI=[1.000,1.000]
- llama3.1:8b: Q_sem=0.972 Q_strict=0.917 n=12/12 cases=12 coverage=1.000 CI=[0.917,1.000]
- qwen2.5-coder:7b: Q_sem=0.917 Q_strict=0.750 n=12/12 cases=12 coverage=1.000 CI=[0.750,1.000]
- granite-code:8b-instruct: Q_sem=0.875 Q_strict=0.000 n=12/12 cases=12 coverage=1.000 CI=[0.736,1.000]
- deepseek-r1:8b: Q_sem=0.635 Q_strict=0.333 n=12/12 cases=12 coverage=1.000 CI=[0.385,0.885]
- qwen3:1.7b: Q_sem=0.583 Q_strict=0.583 n=12/12 cases=12 coverage=1.000 CI=[0.333,0.833]
- qwen3.5:4b: Q_sem=0.417 Q_strict=0.417 n=12/12 cases=12 coverage=1.000 CI=[0.167,0.667]
- command-r7b:7b: Q_sem=1.000 Q_strict=0.375 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=1.000 Q_strict=1.000 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=1.000 Q_strict=0.500 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.875 Q_strict=0.875 n=8/12 cases=12 coverage=0.667 CI=[0.625,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=granite-code:8b-instruct vs phi4-mini:latest, common_n=12)
### HOME-07
- qwen3.5:4b: Q_sem=1.000 Q_strict=0.312 n=16/16 cases=16 coverage=1.000 CI=[1.000,1.000]
- qwen2.5vl:7b: Q_sem=0.875 Q_strict=0.875 n=16/16 cases=16 coverage=1.000 CI=[0.688,1.000]
- granite3.2-vision:2b: Q_sem=0.000 Q_strict=0.000 n=16/16 cases=16 coverage=1.000 CI=[0.000,0.000]
- gemma3:12b: Q_sem=1.000 Q_strict=0.200 n=10/16 cases=16 coverage=0.625 CI=[1.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_LOSS (best=granite3.2-vision:2b vs qwen3.5:4b, common_n=16)
### HOME-08
- llama-guard3:8b: Q_sem=0.938 Q_strict=0.938 n=32/32 cases=32 coverage=1.000 CI=[0.844,1.000]
- qwen3.5:4b: Q_sem=0.906 Q_strict=0.906 n=32/32 cases=32 coverage=1.000 CI=[0.812,1.000]
- lfm2.5:8b: Q_sem=0.812 Q_strict=0.812 n=32/32 cases=32 coverage=1.000 CI=[0.688,0.938]
- llama3.1:8b: Q_sem=0.750 Q_strict=0.750 n=32/32 cases=32 coverage=1.000 CI=[0.594,0.906]
- phi4-mini:latest: Q_sem=0.719 Q_strict=0.000 n=32/32 cases=32 coverage=1.000 CI=[0.562,0.875]
- qwen3:1.7b: Q_sem=0.438 Q_strict=0.438 n=32/32 cases=32 coverage=1.000 CI=[0.281,0.594]
- qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=16/32 cases=32 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.938 Q_strict=0.312 n=16/32 cases=32 coverage=0.500 CI=[0.812,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=0.938 Q_strict=0.000 n=16/32 cases=32 coverage=0.500 CI=[0.812,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.938 Q_strict=0.938 n=16/32 cases=32 coverage=0.500 CI=[0.812,1.000] [insufficient coverage - not ranked]
- aya-expanse:8b: Q_sem=0.875 Q_strict=0.688 n=16/32 cases=32 coverage=0.500 CI=[0.688,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.875 Q_strict=0.875 n=16/32 cases=32 coverage=0.500 CI=[0.688,1.000] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.000 Q_strict=0.000 n=16/32 cases=32 coverage=0.500 CI=[0.000,0.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=llama-guard3:8b vs qwen3.5:4b, common_n=32)
### HOME-09
- llama3.1:8b: Q_sem=1.000 Q_strict=1.000 n=8/8 cases=8 coverage=1.000 CI=[1.000,1.000]
- qwen3.5:4b: Q_sem=1.000 Q_strict=1.000 n=8/8 cases=8 coverage=1.000 CI=[1.000,1.000]
- qwen3:1.7b: Q_sem=0.625 Q_strict=0.625 n=8/8 cases=8 coverage=1.000 CI=[0.250,0.875]
- lfm2.5:8b: Q_sem=0.375 Q_strict=0.375 n=8/8 cases=8 coverage=1.000 CI=[0.125,0.750]
- phi4-mini:latest: Q_sem=0.375 Q_strict=0.375 n=8/8 cases=8 coverage=1.000 CI=[0.125,0.750]
- deepseek-r1:8b: Q_sem=1.000 Q_strict=1.000 n=4/8 cases=8 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=1.000 Q_strict=0.000 n=4/8 cases=8 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=4/8 cases=8 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=4/8 cases=8 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.500 Q_strict=0.500 n=4/8 cases=8 coverage=0.500 CI=[0.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=llama3.1:8b vs qwen3.5:4b, common_n=8)
### HOME-10
- llama3.1:8b: Q_sem=0.042 Q_strict=0.000 n=3/3 cases=3 coverage=1.000 CI=[0.000,0.083]
- mistral-nemo:12b: Q_sem=0.042 Q_strict=0.000 n=3/3 cases=3 coverage=1.000 CI=[0.000,0.125]
- lfm2.5:8b: Q_sem=0.000 Q_strict=0.000 n=3/3 cases=3 coverage=1.000 CI=[0.000,0.000]
- phi4-mini:latest: Q_sem=0.000 Q_strict=0.000 n=3/3 cases=3 coverage=1.000 CI=[0.000,0.000]
- deepseek-r1:8b: Q_sem=0.000 Q_strict=0.000 n=2/3 cases=3 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- qwen3.5:4b: Q_sem=0.000 Q_strict=0.000 n=2/3 cases=3 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- qwen3:1.7b: Q_sem=0.000 Q_strict=0.000 n=2/3 cases=3 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.000 Q_strict=0.000 n=2/3 cases=3 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.000 Q_strict=0.000 n=2/3 cases=3 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=0.000 Q_strict=0.000 n=0/3 cases=3 coverage=0.000 CI=[0.000,0.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=mistral-nemo:12b vs llama3.1:8b, common_n=3)
### HOME-11
- nomic-embed-text:latest: Q_sem=0.980 Q_strict=0.980 n=30/30 cases=30 coverage=1.000 CI=[0.959,1.000]
- bge-m3:latest: Q_sem=0.955 Q_strict=0.955 n=30/30 cases=30 coverage=1.000 CI=[0.921,0.985]
- UNSUPPORTED (not ranked): aya-expanse:8b, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=nomic-embed-text:latest vs bge-m3:latest, common_n=30)
### HOME-12
- llama3.1:8b: Q_sem=1.000 Q_strict=1.000 n=12/12 cases=12 coverage=1.000 CI=[1.000,1.000]
- qwen3:1.7b: Q_sem=0.984 Q_strict=0.984 n=12/12 cases=12 coverage=1.000 CI=[0.965,1.000]
- qwen3.5:4b: Q_sem=0.976 Q_strict=0.976 n=12/12 cases=12 coverage=1.000 CI=[0.952,1.000]
- phi4-mini:latest: Q_sem=0.973 Q_strict=0.973 n=12/12 cases=12 coverage=1.000 CI=[0.944,1.000]
- nuextract:3.8b: Q_sem=0.935 Q_strict=0.935 n=12/12 cases=12 coverage=1.000 CI=[0.895,0.976]
- qwen2.5-coder:7b: Q_sem=0.932 Q_strict=0.932 n=12/12 cases=12 coverage=1.000 CI=[0.892,0.969]
- lfm2.5:8b: Q_sem=0.905 Q_strict=0.905 n=12/12 cases=12 coverage=1.000 CI=[0.839,0.958]
- gemma3:12b: Q_sem=1.000 Q_strict=0.000 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.965 Q_strict=0.965 n=8/12 cases=12 coverage=0.667 CI=[0.932,1.000] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.958 Q_strict=0.958 n=8/12 cases=12 coverage=0.667 CI=[0.917,1.000] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.940 Q_strict=0.690 n=8/12 cases=12 coverage=0.667 CI=[0.884,0.984] [insufficient coverage - not ranked]
- aya-expanse:8b: Q_sem=0.900 Q_strict=0.583 n=8/12 cases=12 coverage=0.667 CI=[0.856,0.947] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.250 Q_strict=0.250 n=8/12 cases=12 coverage=0.667 CI=[0.000,0.500] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_LOSS (best=nuextract:3.8b vs llama3.1:8b, common_n=12)
### HOME-13
- lfm2.5:8b: Q_sem=1.000 Q_strict=1.000 n=20/20 cases=20 coverage=1.000 CI=[1.000,1.000]
- qwen3.5:4b: Q_sem=1.000 Q_strict=1.000 n=20/20 cases=20 coverage=1.000 CI=[1.000,1.000]
- qwen3:1.7b: Q_sem=1.000 Q_strict=1.000 n=20/20 cases=20 coverage=1.000 CI=[1.000,1.000]
- qwen2.5-coder:7b: Q_sem=0.950 Q_strict=0.950 n=20/20 cases=20 coverage=1.000 CI=[0.850,1.000]
- phi4-mini:latest: Q_sem=0.900 Q_strict=0.900 n=20/20 cases=20 coverage=1.000 CI=[0.750,1.000]
- llama3.1:8b: Q_sem=0.850 Q_strict=0.850 n=20/20 cases=20 coverage=1.000 CI=[0.700,1.000]
- command-r7b:7b: Q_sem=1.000 Q_strict=0.300 n=10/20 cases=20 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=1.000 Q_strict=1.000 n=10/20 cases=20 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=10/20 cases=20 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.900 Q_strict=0.600 n=10/20 cases=20 coverage=0.500 CI=[0.700,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.900 Q_strict=0.900 n=10/20 cases=20 coverage=0.500 CI=[0.700,1.000] [insufficient coverage - not ranked]
- aya-expanse:8b: Q_sem=0.800 Q_strict=0.600 n=10/20 cases=20 coverage=0.500 CI=[0.500,1.000] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.800 Q_strict=0.800 n=10/20 cases=20 coverage=0.500 CI=[0.500,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=phi4-mini:latest vs lfm2.5:8b, common_n=20)
### HOME-14
- phi4-mini:latest: Q_sem=0.970 Q_strict=0.812 n=16/16 cases=16 coverage=1.000 CI=[0.935,1.000]
- qwen2.5-coder:7b: Q_sem=0.865 Q_strict=0.750 n=16/16 cases=16 coverage=1.000 CI=[0.730,0.972]
- granite-code:8b-instruct: Q_sem=0.806 Q_strict=0.000 n=16/16 cases=16 coverage=1.000 CI=[0.657,0.945]
- llama3.1:8b: Q_sem=0.769 Q_strict=0.438 n=16/16 cases=16 coverage=1.000 CI=[0.568,0.934]
- qwen3:1.7b: Q_sem=0.602 Q_strict=0.500 n=16/16 cases=16 coverage=1.000 CI=[0.367,0.828]
- qwen3.5:4b: Q_sem=0.445 Q_strict=0.438 n=16/16 cases=16 coverage=1.000 CI=[0.250,0.688]
- gemma3:12b: Q_sem=0.958 Q_strict=0.750 n=8/16 cases=16 coverage=0.500 CI=[0.903,1.000] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.957 Q_strict=0.625 n=8/16 cases=16 coverage=0.500 CI=[0.913,0.986] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.866 Q_strict=0.625 n=8/16 cases=16 coverage=0.500 CI=[0.710,0.972] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.750 Q_strict=0.750 n=8/16 cases=16 coverage=0.500 CI=[0.375,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.625 Q_strict=0.625 n=8/16 cases=16 coverage=0.500 CI=[0.250,0.875] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.125 Q_strict=0.000 n=8/16 cases=16 coverage=0.500 CI=[0.000,0.375] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=qwen2.5-coder:7b vs phi4-mini:latest, common_n=16)
### HOME-15
- qwen2.5vl:7b: Q_sem=0.500 Q_strict=0.000 n=12/12 cases=12 coverage=1.000 CI=[0.250,0.750]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-16
- qwen3.5:4b: Q_sem=0.875 Q_strict=0.875 n=40/40 cases=40 coverage=1.000 CI=[0.775,0.975]
- lfm2.5:8b: Q_sem=0.825 Q_strict=0.825 n=40/40 cases=40 coverage=1.000 CI=[0.700,0.925]
- llama3.1:8b: Q_sem=0.825 Q_strict=0.825 n=40/40 cases=40 coverage=1.000 CI=[0.700,0.925]
- qwen3:1.7b: Q_sem=0.800 Q_strict=0.800 n=40/40 cases=40 coverage=1.000 CI=[0.675,0.925]
- phi4-mini:latest: Q_sem=0.600 Q_strict=0.000 n=40/40 cases=40 coverage=1.000 CI=[0.450,0.750]
- gemma3:12b: Q_sem=0.950 Q_strict=0.050 n=20/40 cases=40 coverage=0.500 CI=[0.850,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.950 Q_strict=0.950 n=20/40 cases=40 coverage=0.500 CI=[0.850,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.950 Q_strict=0.950 n=20/40 cases=40 coverage=0.500 CI=[0.850,1.000] [insufficient coverage - not ranked]
- aya-expanse:8b: Q_sem=0.900 Q_strict=0.000 n=20/40 cases=40 coverage=0.500 CI=[0.750,1.000] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.850 Q_strict=0.750 n=20/40 cases=40 coverage=0.500 CI=[0.700,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.850 Q_strict=0.850 n=20/40 cases=40 coverage=0.500 CI=[0.700,1.000] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.800 Q_strict=0.550 n=20/40 cases=40 coverage=0.500 CI=[0.600,0.950] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=qwen3:1.7b vs qwen3.5:4b, common_n=40)
### HOME-17
- qwen3:14b: Q_sem=0.500 Q_strict=0.500 n=6/6 cases=6 coverage=1.000 CI=[0.167,0.833]
- lfm2.5:8b: Q_sem=0.333 Q_strict=0.333 n=6/6 cases=6 coverage=1.000 CI=[0.000,0.667]
- qwen3:1.7b: Q_sem=0.333 Q_strict=0.333 n=6/6 cases=6 coverage=1.000 CI=[0.000,0.667]
- phi4-mini:latest: Q_sem=0.167 Q_strict=0.000 n=6/6 cases=6 coverage=1.000 CI=[0.000,0.500]
- qwen2.5-coder:7b: Q_sem=0.000 Q_strict=0.000 n=6/6 cases=6 coverage=1.000 CI=[0.000,0.000]
- qwen3.5:4b: Q_sem=0.000 Q_strict=0.000 n=6/6 cases=6 coverage=1.000 CI=[0.000,0.000]
- qwen3:8b: Q_sem=0.750 Q_strict=0.750 n=4/6 cases=6 coverage=0.667 CI=[0.250,1.000] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.250 Q_strict=0.250 n=4/6 cases=6 coverage=0.667 CI=[0.000,0.750] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=0.000 Q_strict=0.000 n=4/6 cases=6 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- llama3.1:8b: Q_sem=0.000 Q_strict=0.000 n=4/6 cases=6 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.000 Q_strict=0.000 n=4/6 cases=6 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=qwen3:14b vs lfm2.5:8b, common_n=6)
### HOME-18
- llama3.1:8b: Q_sem=0.850 Q_strict=0.800 n=10/10 cases=10 coverage=1.000 CI=[0.600,1.000]
- qwen3:1.7b: Q_sem=0.850 Q_strict=0.700 n=10/10 cases=10 coverage=1.000 CI=[0.700,1.000]
- qwen3:8b: Q_sem=0.850 Q_strict=0.800 n=10/10 cases=10 coverage=1.000 CI=[0.600,1.000]
- lfm2.5:8b: Q_sem=0.550 Q_strict=0.400 n=10/10 cases=10 coverage=1.000 CI=[0.300,0.800]
- phi4-mini:latest: Q_sem=0.450 Q_strict=0.100 n=10/10 cases=10 coverage=1.000 CI=[0.250,0.650]
- qwen3.5:4b: Q_sem=0.450 Q_strict=0.400 n=10/10 cases=10 coverage=1.000 CI=[0.150,0.750]
- mistral-nemo:12b: Q_sem=1.000 Q_strict=1.000 n=6/10 cases=10 coverage=0.600 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=6/10 cases=10 coverage=0.600 CI=[1.000,1.000] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.333 Q_strict=0.000 n=6/10 cases=10 coverage=0.600 CI=[0.167,0.500] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.333 Q_strict=0.000 n=6/10 cases=10 coverage=0.600 CI=[0.167,0.500] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=qwen3:8b vs qwen3:1.7b, common_n=10)
### HOME-19
- qwen3.5:4b: Q_sem=0.959 Q_strict=0.959 n=8/8 cases=8 coverage=1.000 CI=[0.945,0.971]
- qwen2.5-coder:7b: Q_sem=0.949 Q_strict=0.949 n=8/8 cases=8 coverage=1.000 CI=[0.912,0.971]
- reader-lm:1.5b: Q_sem=0.917 Q_strict=0.917 n=8/8 cases=8 coverage=1.000 CI=[0.911,0.923]
- llama3.1:8b: Q_sem=0.888 Q_strict=0.888 n=8/8 cases=8 coverage=1.000 CI=[0.865,0.914]
- phi4-mini:latest: Q_sem=0.874 Q_strict=0.874 n=8/8 cases=8 coverage=1.000 CI=[0.788,0.935]
- qwen3:1.7b: Q_sem=0.683 Q_strict=0.683 n=8/8 cases=8 coverage=1.000 CI=[0.556,0.802]
- lfm2.5:8b: Q_sem=0.517 Q_strict=0.517 n=8/8 cases=8 coverage=1.000 CI=[0.388,0.635]
- qwen3:8b: Q_sem=0.970 Q_strict=0.970 n=4/8 cases=8 coverage=0.500 CI=[0.963,0.978] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.963 Q_strict=0.963 n=4/8 cases=8 coverage=0.500 CI=[0.958,0.968] [insufficient coverage - not ranked]
- qwen3:14b: Q_sem=0.955 Q_strict=0.955 n=4/8 cases=8 coverage=0.500 CI=[0.918,0.980] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.948 Q_strict=0.948 n=4/8 cases=8 coverage=0.500 CI=[0.905,0.979] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=0.824 Q_strict=0.824 n=4/8 cases=8 coverage=0.500 CI=[0.820,0.828] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, sqlcoder:7b
  HOME verdict: HOME_LOSS (best=reader-lm:1.5b vs qwen3.5:4b, common_n=8)
### HOME-20
- phi4-mini:latest: Q_sem=0.937 Q_strict=0.850 n=20/20 cases=20 coverage=1.000 CI=[0.836,1.000]
- qwen2.5-coder:7b: Q_sem=0.937 Q_strict=0.850 n=20/20 cases=20 coverage=1.000 CI=[0.830,1.000]
- qwen3.5:4b: Q_sem=0.769 Q_strict=0.700 n=20/20 cases=20 coverage=1.000 CI=[0.589,0.925]
- lfm2.5:8b: Q_sem=0.737 Q_strict=0.650 n=20/20 cases=20 coverage=1.000 CI=[0.528,0.900]
- llama3.1:8b: Q_sem=0.705 Q_strict=0.650 n=20/20 cases=20 coverage=1.000 CI=[0.505,0.871]
- qwen3:1.7b: Q_sem=0.654 Q_strict=0.550 n=20/20 cases=20 coverage=1.000 CI=[0.450,0.841]
- sqlcoder:7b: Q_sem=0.559 Q_strict=0.450 n=20/20 cases=20 coverage=1.000 CI=[0.346,0.763]
- qwen3:14b: Q_sem=0.979 Q_strict=0.833 n=12/20 cases=20 coverage=0.600 CI=[0.948,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.896 Q_strict=0.750 n=12/20 cases=20 coverage=0.600 CI=[0.720,1.000] [insufficient coverage - not ranked]
- gemma3:12b: Q_sem=0.882 Q_strict=0.667 n=12/20 cases=20 coverage=0.600 CI=[0.704,0.988] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.855 Q_strict=0.750 n=12/20 cases=20 coverage=0.600 CI=[0.667,0.986] [insufficient coverage - not ranked]
- granite-code:8b-instruct: Q_sem=0.786 Q_strict=0.333 n=12/20 cases=20 coverage=0.600 CI=[0.536,1.000] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.583 Q_strict=0.583 n=12/20 cases=20 coverage=0.600 CI=[0.333,0.833] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.333 Q_strict=0.333 n=12/20 cases=20 coverage=0.600 CI=[0.083,0.583] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b
  HOME verdict: HOME_LOSS (best=sqlcoder:7b vs phi4-mini:latest, common_n=20)
### HOME-21
- qwen3.5:4b: Q_sem=0.625 Q_strict=0.125 n=8/8 cases=8 coverage=1.000 CI=[0.312,0.875]
- qwen3:1.7b: Q_sem=0.562 Q_strict=0.375 n=8/8 cases=8 coverage=1.000 CI=[0.312,0.875]
- lfm2.5:8b: Q_sem=0.375 Q_strict=0.250 n=8/8 cases=8 coverage=1.000 CI=[0.125,0.688]
- phi4-mini:latest: Q_sem=0.250 Q_strict=0.000 n=8/8 cases=8 coverage=1.000 CI=[0.062,0.438]
- qwen3:14b: Q_sem=0.800 Q_strict=0.800 n=5/8 cases=8 coverage=0.625 CI=[0.400,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=0.500 Q_strict=0.400 n=5/8 cases=8 coverage=0.625 CI=[0.100,0.900] [insufficient coverage - not ranked]
- llama3.1:8b: Q_sem=0.400 Q_strict=0.200 n=5/8 cases=8 coverage=0.625 CI=[0.100,0.700] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.400 Q_strict=0.200 n=5/8 cases=8 coverage=0.625 CI=[0.100,0.700] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.300 Q_strict=0.000 n=5/8 cases=8 coverage=0.625 CI=[0.100,0.500] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.300 Q_strict=0.000 n=5/8 cases=8 coverage=0.625 CI=[0.100,0.500] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=lfm2.5:8b vs qwen3.5:4b, common_n=8)
### HOME-22
- qwen3.5:4b: Q_sem=0.900 Q_strict=0.900 n=10/10 cases=10 coverage=1.000 CI=[0.700,1.000]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-23
- qwen2.5vl:7b: Q_sem=0.987 Q_strict=0.937 n=16/16 cases=16 coverage=1.000 CI=[0.963,1.000]
- qwen3.5:4b: Q_sem=0.984 Q_strict=0.875 n=16/16 cases=16 coverage=1.000 CI=[0.959,1.000]
- glm-ocr:latest: Q_sem=0.945 Q_strict=0.188 n=16/16 cases=16 coverage=1.000 CI=[0.884,0.988]
- granite3.2-vision:2b: Q_sem=0.718 Q_strict=0.495 n=16/16 cases=16 coverage=1.000 CI=[0.530,0.896]
- gemma3:12b: Q_sem=0.979 Q_strict=0.899 n=10/16 cases=16 coverage=0.625 CI=[0.941,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, granite-code:8b-instruct, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_LOSS (best=glm-ocr:latest vs qwen2.5vl:7b, common_n=16)
### HOME-24
- lfm2.5:8b: Q_sem=1.000 Q_strict=1.000 n=30/30 cases=30 coverage=1.000 CI=[1.000,1.000]
- qwen3.5:4b: Q_sem=0.967 Q_strict=0.933 n=30/30 cases=30 coverage=1.000 CI=[0.900,1.000]
- qwen3:1.7b: Q_sem=0.967 Q_strict=0.967 n=30/30 cases=30 coverage=1.000 CI=[0.900,1.000]
- llama3.1:8b: Q_sem=0.600 Q_strict=0.600 n=30/30 cases=30 coverage=1.000 CI=[0.433,0.767]
- functiongemma:270m: Q_sem=0.433 Q_strict=0.367 n=30/30 cases=30 coverage=1.000 CI=[0.267,0.600]
- phi4-mini:latest: Q_sem=0.367 Q_strict=0.333 n=30/30 cases=30 coverage=1.000 CI=[0.200,0.533]
- qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=15/30 cases=30 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=15/30 cases=30 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- mistral-nemo:12b: Q_sem=0.867 Q_strict=0.867 n=15/30 cases=30 coverage=0.500 CI=[0.667,1.000] [insufficient coverage - not ranked]
- command-r7b:7b: Q_sem=0.333 Q_strict=0.333 n=15/30 cases=30 coverage=0.500 CI=[0.133,0.600] [insufficient coverage - not ranked]
- deepseek-r1:8b: Q_sem=0.333 Q_strict=0.333 n=15/30 cases=30 coverage=0.500 CI=[0.133,0.600] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_LOSS (best=functiongemma:270m vs lfm2.5:8b, common_n=30)

## DEFERRED
- BGE-Reranker-v2-m3: Specialist not installed (NIGHT-1 Ollama only; reported as DEFERRED)
- DeepSeek-OCR: Specialist not installed (NIGHT-1 Ollama only; reported as DEFERRED)
- Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf: LM Studio runtime not initialized (NIGHT-1 Ollama only; reported as DEFERRED)
- Kokoro-TTS: Specialist not installed (NIGHT-1 Ollama only; reported as DEFERRED)
- Ministral-3-8B-Instruct-2512-Q4_K_M.gguf (+ mmproj F16): LM Studio runtime not initialized (NIGHT-1 Ollama only; reported as DEFERRED)
- Nomic-Embed-Code: Specialist not installed (NIGHT-1 Ollama only; reported as DEFERRED)
- Phi-4-Multimodal: Specialist not installed (NIGHT-1 Ollama only; reported as DEFERRED)
- Qwen3-ASR-1.7B: Specialist not installed (NIGHT-1 Ollama only; reported as DEFERRED)
- Qwen3-VL-8B-Instruct-Q4_K_M.gguf (+ mmproj F16): LM Studio runtime not initialized (NIGHT-1 Ollama only; reported as DEFERRED)
- Qwen3.5-35B-A3B-Q3_K_M.gguf: LM Studio runtime not initialized (NIGHT-1 Ollama only; reported as DEFERRED)
- Qwen3.5-9B-Q4_K_M.gguf: LM Studio runtime not initialized (NIGHT-1 Ollama only; reported as DEFERRED)
- gpt-oss-20b-MXFP4.gguf: LM Studio runtime not initialized (NIGHT-1 Ollama only; reported as DEFERRED)
