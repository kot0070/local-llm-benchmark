# NIGHT-1 summary

## Run overview

- models run: 28 (aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-ministral-3-8b:q4km, night2-nomic-embed-code:q4km, night2-qwen3-vl-8b:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b)
- tests run: 25 (HOME-01, HOME-02, HOME-03, HOME-04, HOME-05, HOME-06, HOME-07, HOME-08, HOME-09, HOME-10, HOME-11, HOME-12, HOME-13, HOME-14, HOME-15, HOME-16, HOME-17, HOME-18, HOME-19, HOME-20, HOME-21, HOME-22, HOME-23, HOME-24, PERF)
- records: 1810
- wall time total (sum wall_s): 18012.9 s
- NOT_RUN_BUDGET: 238
- counts by status:
  - CONTEXT_OVERFLOW: 4
  - FORMAT_ERROR: 158
  - NOT_RUN_BUDGET: 238
  - OK: 657
  - OUTPUT_TRUNCATED: 32
  - TIMEOUT: 4
  - UNSUPPORTED_CAPABILITY: 609
  - WRONG_ANSWER: 108

## Per-test ranking (by Q_sem)
### HOME-01
- night2-qwen3.5-9b:q4km: Q_sem=0.993 Q_strict=0.993 n=24/24 cases=24 coverage=1.000 CI=[0.979,1.000]
- night2-ministral-3-8b:q4km: Q_sem=0.941 Q_strict=0.000 n=24/24 cases=24 coverage=1.000 CI=[0.910,0.972]
- night2-qwen3-vl-8b:q4km: Q_sem=0.986 Q_strict=0.986 n=12/24 cases=24 coverage=0.500 CI=[0.972,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_WIN (best=night2-qwen3.5-9b:q4km vs night2-ministral-3-8b:q4km, common_n=24)
### HOME-02
- night2-nomic-embed-code:q4km: Q_sem=0.781 Q_strict=0.781 n=40/40 cases=40 coverage=1.000 CI=[0.680,0.877]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-ministral-3-8b:q4km, night2-qwen3-vl-8b:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-03
- night2-ministral-3-8b:q4km: Q_sem=1.000 Q_strict=0.000 n=16/16 cases=16 coverage=1.000 CI=[1.000,1.000]
- night2-qwen3.5-9b:q4km: Q_sem=0.875 Q_strict=0.875 n=16/16 cases=16 coverage=1.000 CI=[0.688,1.000]
- night2-qwen3-vl-8b:q4km: Q_sem=0.900 Q_strict=0.900 n=10/16 cases=16 coverage=0.625 CI=[0.700,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3.5-9b:q4km, common_n=16)
### HOME-04
- night2-qwen3.5-9b:q4km: Q_sem=0.333 Q_strict=0.333 n=12/12 cases=12 coverage=1.000 CI=[0.083,0.583]
- night2-qwen3-vl-8b:q4km: Q_sem=1.000 Q_strict=1.000 n=6/12 cases=12 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- night2-ministral-3-8b:q4km: Q_sem=0.667 Q_strict=0.667 n=6/12 cases=12 coverage=0.500 CI=[0.333,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3-vl-8b:q4km vs night2-ministral-3-8b:q4km, common_n=6)
### HOME-05
- night2-ministral-3-8b:q4km: Q_sem=0.417 Q_strict=0.000 n=12/12 cases=12 coverage=1.000 CI=[0.167,0.667]
- night2-qwen3-vl-8b:q4km: Q_sem=0.500 Q_strict=0.500 n=8/12 cases=12 coverage=0.667 CI=[0.125,0.875] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3-vl-8b:q4km, common_n=8)
### HOME-06
- night2-ministral-3-8b:q4km: Q_sem=0.917 Q_strict=0.833 n=12/12 cases=12 coverage=1.000 CI=[0.750,1.000]
- night2-qwen3.5-9b:q4km: Q_sem=0.333 Q_strict=0.333 n=12/12 cases=12 coverage=1.000 CI=[0.083,0.583]
- night2-qwen3-vl-8b:q4km: Q_sem=1.000 Q_strict=0.875 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_WIN (best=night2-ministral-3-8b:q4km vs night2-qwen3.5-9b:q4km, common_n=12)
### HOME-07
- night2-ministral-3-8b:q4km: Q_sem=1.000 Q_strict=0.000 n=10/16 cases=16 coverage=0.625 CI=[1.000,1.000] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=1.000 Q_strict=1.000 n=10/16 cases=16 coverage=0.625 CI=[1.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3-vl-8b:q4km, common_n=10)
### HOME-08
- night2-ministral-3-8b:q4km: Q_sem=1.000 Q_strict=0.000 n=32/32 cases=32 coverage=1.000 CI=[1.000,1.000]
- night2-qwen3.5-9b:q4km: Q_sem=0.969 Q_strict=0.969 n=32/32 cases=32 coverage=1.000 CI=[0.906,1.000]
- night2-qwen3-vl-8b:q4km: Q_sem=1.000 Q_strict=1.000 n=16/32 cases=32 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3.5-9b:q4km, common_n=32)
### HOME-09
- night2-qwen3.5-9b:q4km: Q_sem=1.000 Q_strict=1.000 n=8/8 cases=8 coverage=1.000 CI=[1.000,1.000]
- night2-ministral-3-8b:q4km: Q_sem=1.000 Q_strict=0.000 n=4/8 cases=8 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=1.000 Q_strict=1.000 n=4/8 cases=8 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3.5-9b:q4km vs night2-ministral-3-8b:q4km, common_n=4)
### HOME-10
- night2-qwen3-vl-8b:q4km: Q_sem=0.000 Q_strict=0.000 n=2/3 cases=3 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- night2-qwen3.5-9b:q4km: Q_sem=0.000 Q_strict=0.000 n=2/3 cases=3 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- night2-ministral-3-8b:q4km: Q_sem=0.000 Q_strict=0.000 n=1/3 cases=3 coverage=0.333 CI=[0.000,0.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3.5-9b:q4km vs night2-ministral-3-8b:q4km, common_n=1)
### HOME-11
- night2-nomic-embed-code:q4km: Q_sem=0.902 Q_strict=0.902 n=30/30 cases=30 coverage=1.000 CI=[0.845,0.956]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-ministral-3-8b:q4km, night2-qwen3-vl-8b:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-12
- night2-ministral-3-8b:q4km: Q_sem=1.000 Q_strict=0.000 n=12/12 cases=12 coverage=1.000 CI=[1.000,1.000]
- night2-qwen3.5-9b:q4km: Q_sem=0.993 Q_strict=0.993 n=12/12 cases=12 coverage=1.000 CI=[0.979,1.000]
- night2-qwen3-vl-8b:q4km: Q_sem=1.000 Q_strict=1.000 n=8/12 cases=12 coverage=0.667 CI=[1.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3.5-9b:q4km, common_n=12)
### HOME-13
- night2-qwen3.5-9b:q4km: Q_sem=1.000 Q_strict=1.000 n=20/20 cases=20 coverage=1.000 CI=[1.000,1.000]
- night2-ministral-3-8b:q4km: Q_sem=1.000 Q_strict=1.000 n=10/20 cases=20 coverage=0.500 CI=[1.000,1.000] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=0.900 Q_strict=0.900 n=10/20 cases=20 coverage=0.500 CI=[0.700,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3.5-9b:q4km vs night2-ministral-3-8b:q4km, common_n=10)
### HOME-14
- night2-qwen3.5-9b:q4km: Q_sem=0.867 Q_strict=0.812 n=16/16 cases=16 coverage=1.000 CI=[0.688,1.000]
- night2-ministral-3-8b:q4km: Q_sem=0.917 Q_strict=0.750 n=8/16 cases=16 coverage=0.500 CI=[0.778,1.000] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=0.832 Q_strict=0.625 n=8/16 cases=16 coverage=0.500 CI=[0.569,0.984] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3-vl-8b:q4km, common_n=8)
### HOME-15
- night2-ministral-3-8b:q4km: Q_sem=0.083 Q_strict=0.000 n=12/12 cases=12 coverage=1.000 CI=[0.000,0.250]
- night2-qwen3-vl-8b:q4km: Q_sem=0.000 Q_strict=0.000 n=12/12 cases=12 coverage=1.000 CI=[0.000,0.000]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3-vl-8b:q4km, common_n=12)
### HOME-16
- night2-qwen3.5-9b:q4km: Q_sem=0.868 Q_strict=0.868 n=38/40 cases=40 coverage=0.950 CI=[0.763,0.974]
- night2-qwen3-vl-8b:q4km: Q_sem=0.900 Q_strict=0.900 n=20/40 cases=40 coverage=0.500 CI=[0.750,1.000] [insufficient coverage - not ranked]
- night2-ministral-3-8b:q4km: Q_sem=0.800 Q_strict=0.000 n=20/40 cases=40 coverage=0.500 CI=[0.600,0.950] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3.5-9b:q4km vs night2-qwen3-vl-8b:q4km, common_n=18)
### HOME-17
- night2-qwen3.5-9b:q4km: Q_sem=0.000 Q_strict=0.000 n=6/6 cases=6 coverage=1.000 CI=[0.000,0.000]
- night2-ministral-3-8b:q4km: Q_sem=0.250 Q_strict=0.000 n=4/6 cases=6 coverage=0.667 CI=[0.000,0.750] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=0.000 Q_strict=0.000 n=4/6 cases=6 coverage=0.667 CI=[0.000,0.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3.5-9b:q4km, common_n=4)
### HOME-18
- night2-qwen3.5-9b:q4km: Q_sem=0.750 Q_strict=0.700 n=10/10 cases=10 coverage=1.000 CI=[0.500,1.000]
- night2-ministral-3-8b:q4km: Q_sem=1.000 Q_strict=0.500 n=6/10 cases=10 coverage=0.600 CI=[1.000,1.000] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=1.000 Q_strict=1.000 n=6/10 cases=10 coverage=0.600 CI=[1.000,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3-vl-8b:q4km, common_n=6)
### HOME-19
- night2-qwen3.5-9b:q4km: Q_sem=0.980 Q_strict=0.980 n=8/8 cases=8 coverage=1.000 CI=[0.978,0.982]
- night2-qwen3-vl-8b:q4km: Q_sem=0.962 Q_strict=0.962 n=4/8 cases=8 coverage=0.500 CI=[0.946,0.978] [insufficient coverage - not ranked]
- night2-ministral-3-8b:q4km: Q_sem=0.960 Q_strict=0.000 n=4/8 cases=8 coverage=0.500 CI=[0.935,0.976] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3.5-9b:q4km vs night2-qwen3-vl-8b:q4km, common_n=4)
### HOME-20
- night2-qwen3.5-9b:q4km: Q_sem=0.943 Q_strict=0.900 n=20/20 cases=20 coverage=1.000 CI=[0.836,1.000]
- night2-qwen3-vl-8b:q4km: Q_sem=0.896 Q_strict=0.750 n=12/20 cases=20 coverage=0.600 CI=[0.720,1.000] [insufficient coverage - not ranked]
- night2-ministral-3-8b:q4km: Q_sem=0.873 Q_strict=0.750 n=12/20 cases=20 coverage=0.600 CI=[0.702,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3.5-9b:q4km vs night2-qwen3-vl-8b:q4km, common_n=12)
### HOME-21
- night2-qwen3.5-9b:q4km: Q_sem=0.812 Q_strict=0.750 n=8/8 cases=8 coverage=1.000 CI=[0.562,1.000]
- night2-ministral-3-8b:q4km: Q_sem=0.900 Q_strict=0.400 n=5/8 cases=8 coverage=0.625 CI=[0.700,1.000] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=0.800 Q_strict=0.800 n=5/8 cases=8 coverage=0.625 CI=[0.400,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3.5-9b:q4km, common_n=5)
### HOME-22
- night2-qwen3-vl-8b:q4km: Q_sem=0.800 Q_strict=0.800 n=10/10 cases=10 coverage=1.000 CI=[0.500,1.000]
- night2-ministral-3-8b:q4km: Q_sem=0.700 Q_strict=0.700 n=10/10 cases=10 coverage=1.000 CI=[0.400,1.000]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3-vl-8b:q4km vs night2-ministral-3-8b:q4km, common_n=10)
### HOME-23
- night2-ministral-3-8b:q4km: Q_sem=0.981 Q_strict=0.900 n=10/16 cases=16 coverage=0.625 CI=[0.942,1.000] [insufficient coverage - not ranked]
- night2-qwen3-vl-8b:q4km: Q_sem=0.980 Q_strict=0.899 n=10/16 cases=16 coverage=0.625 CI=[0.940,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, night2-qwen3.5-9b:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-ministral-3-8b:q4km vs night2-qwen3-vl-8b:q4km, common_n=10)
### HOME-24
- night2-qwen3.5-9b:q4km: Q_sem=1.000 Q_strict=0.967 n=30/30 cases=30 coverage=1.000 CI=[1.000,1.000]
- night2-qwen3-vl-8b:q4km: Q_sem=0.929 Q_strict=0.929 n=14/30 cases=30 coverage=0.467 CI=[0.786,1.000] [insufficient coverage - not ranked]
- night2-ministral-3-8b:q4km: Q_sem=0.867 Q_strict=0.867 n=15/30 cases=30 coverage=0.500 CI=[0.667,1.000] [insufficient coverage - not ranked]
- UNSUPPORTED (not ranked): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, night2-nomic-embed-code:q4km, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
  HOME verdict: HOME_TIE (best=night2-qwen3.5-9b:q4km vs night2-qwen3-vl-8b:q4km, common_n=14)

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
