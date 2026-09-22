# OWNER SUMMARY — night_20260921-155146

## 1. Огляд прогону
- run_id: night_20260921-155146
- початок (local): 2026-09-21T16:02:44.014805-05:00
- кінець (local): 2026-09-21T23:44:11.645030-05:00
- тривалість: 461.5 хв
- бюджет: 8.0 год
- Ollama: 0.34.2
- GPU: NVIDIA GeForce RTX 3070, GPU-897afb79-eeae-e49b-f373-0b5b356225b1, 616.92, 8192 MiB, 220.00 W
- CPU: Intel(R) Core(TM) i9-10900KF CPU @ 3.70GHz (зчитано з поточної системи); RAM: 31.9 GB (зчитано з поточної системи); OS: 10.0.26200
- моделей запущено: 24 (aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b)
- тестів запущено: 25 (HOME-01, HOME-02, HOME-03, HOME-04, HOME-05, HOME-06, HOME-07, HOME-08, HOME-09, HOME-10, HOME-11, HOME-12, HOME-13, HOME-14, HOME-15, HOME-16, HOME-17, HOME-18, HOME-19, HOME-20, HOME-21, HOME-22, HOME-23, HOME-24, PERF)
- записів: 4190
- за статусами:
  - CONTEXT_OVERFLOW: 4
  - FORMAT_ERROR: 459
  - NOT_RUN_BUDGET: 799
  - OK: 1755
  - OUTPUT_TRUNCATED: 191
  - UNSUPPORTED_CAPABILITY: 406
  - WRONG_ANSWER: 576
- NOT_RUN_BUDGET: 799
- частковий прогін: 799 записів пропущено через брак часу (NOT_RUN_BUDGET); покриття неповне.

## 2. HOME-вердикти
| Тест | Назва | HOME-модель | HOME Q_sem (n) | Найкращий конкурент | Q_sem (n) | common_n | Вердикт |
|---|---|---|---|---|---|---|---|
| HOME-01 | Multilingual customer message understanding | aya-expanse:8b | 0.858 (24/24) | qwen3.5:4b | 0.944 (24/24) | 24 | HOME програє |
| HOME-02 | Cross-lingual retrieval | bge-m3:latest | 0.923 (40/40) | немає даних | немає даних | немає даних | недостатньо даних |
| HOME-03 | RAG with citations and abstention | command-r7b:7b | 0.000 (16/16) | lfm2.5:8b | 0.938 (16/16) | 16 | HOME програє |
| HOME-04 | Competition math, integer answer in \boxed{} | deepseek-r1:8b | 0.333 (12/12) | lfm2.5:8b | 0.917 (12/12) | 12 | HOME програє |
| HOME-05 | Chart reading | gemma3:12b | 0.333 (12/12) | qwen3.5:4b | 0.500 (12/12) | 12 | нічия |
| HOME-06 | Bug repair with hidden tests and bug-line localisation | granite-code:8b-instruct | 0.875 (12/12) | phi4-mini:latest | 1.000 (12/12) | 12 | нічия |
| HOME-07 | Document understanding | granite3.2-vision:2b | 0.000 (16/16) | qwen3.5:4b | 1.000 (16/16) | 16 | HOME програє |
| HOME-08 | Safety classification | llama-guard3:8b | 0.938 (32/32) | qwen3.5:4b | 0.906 (32/32) | 32 | нічия |
| HOME-09 | Long-context wiki QA | llama3.1:8b | 1.000 (8/8) | qwen3.5:4b | 1.000 (8/8) | 8 | нічия |
| HOME-10 | Multilingual log state tracking | mistral-nemo:12b | 0.042 (3/3) | llama3.1:8b | 0.042 (3/3) | 3 | нічия |
| HOME-11 | English retrieval | nomic-embed-text:latest | 0.980 (30/30) | bge-m3:latest | 0.955 (30/30) | 30 | нічия |
| HOME-12 | Template extraction from long texts | nuextract:3.8b | 0.935 (12/12) | llama3.1:8b | 1.000 (12/12) | 12 | HOME програє |
| HOME-13 | Multi-step word problems, numeric answer in \boxed{} | phi4-mini:latest | 0.900 (20/20) | lfm2.5:8b | 1.000 (20/20) | 20 | нічия |
| HOME-14 | Code generation from spec, hidden tests | qwen2.5-coder:7b | 0.865 (16/16) | phi4-mini:latest | 0.970 (16/16) | 16 | нічия |
| HOME-15 | Visual grounding | qwen2.5vl:7b | 0.500 (12/12) | немає даних | немає даних | немає даних | недостатньо даних |
| HOME-16 | Support request routing with policy | qwen3:1.7b | 0.800 (40/40) | qwen3.5:4b | 0.875 (40/40) | 40 | нічия |
| HOME-17 | Constrained optimisation, JSON solution | qwen3:14b | 0.500 (6/6) | lfm2.5:8b | 0.333 (6/6) | 6 | нічия |
| HOME-18 | Short tool loops | qwen3:8b | 0.850 (10/10) | qwen3:1.7b | 0.850 (10/10) | 10 | нічия |
| HOME-19 | HTML to Markdown conversion | reader-lm:1.5b | 0.917 (8/8) | qwen3.5:4b | 0.959 (8/8) | 8 | HOME програє |
| HOME-20 | Text-to-SQL on retail/hr SQLite databases | sqlcoder:7b | 0.559 (20/20) | phi4-mini:latest | 0.937 (20/20) | 20 | HOME програє |
| HOME-21 | Long tool chains | lfm2.5:8b | 0.375 (8/8) | qwen3.5:4b | 0.625 (8/8) | 8 | нічия |
| HOME-22 | Vision tool calling | qwen3.5:4b | 0.900 (10/10) | немає даних | немає даних | немає даних | недостатньо даних |
| HOME-23 | OCR transcription | glm-ocr:latest | 0.945 (16/16) | qwen2.5vl:7b | 0.987 (16/16) | 16 | HOME програє |
| HOME-24 | Single-turn function calling | functiongemma:270m | 0.433 (30/30) | lfm2.5:8b | 1.000 (30/30) | 30 | HOME програє |
HOME-07: див. також додатковий прогін night_20260921-155146_gv (інший контракт відповіді, не порівнюється напряму) — деталі в ANALYSIS_UK.md.

## 3. Топ-3 по кожному тесту
### HOME-01
- 1. qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=12/24 CI=[1.000,1.000] (покриття < 0.9)
- 2. gemma3:12b: Q_sem=0.986 Q_strict=0.000 n=12/24 CI=[0.972,1.000] (покриття < 0.9)
- 3. qwen3:14b: Q_sem=0.972 Q_strict=0.972 n=12/24 CI=[0.931,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-02
- 1. bge-m3:latest: Q_sem=0.923 Q_strict=0.923 n=40/40 CI=[0.888,0.957]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-03
- 1. deepseek-r1:8b: Q_sem=1.000 Q_strict=0.300 n=10/16 CI=[1.000,1.000] (покриття < 0.9)
- 2. gemma3:12b: Q_sem=1.000 Q_strict=0.000 n=10/16 CI=[1.000,1.000] (покриття < 0.9)
- 3. lfm2.5:8b: Q_sem=0.938 Q_strict=0.938 n=16/16 CI=[0.812,1.000]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-04
- 1. lfm2.5:8b: Q_sem=0.917 Q_strict=0.917 n=12/12 CI=[0.750,1.000]
- 2. qwen3:1.7b: Q_sem=0.833 Q_strict=0.833 n=12/12 CI=[0.583,1.000]
- 3. qwen3:8b: Q_sem=0.667 Q_strict=0.667 n=6/12 CI=[0.333,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, qwen3:14b, reader-lm:1.5b, sqlcoder:7b
### HOME-05
- 1. qwen3.5:4b: Q_sem=0.500 Q_strict=0.250 n=12/12 CI=[0.250,0.833]
- 2. qwen2.5vl:7b: Q_sem=0.417 Q_strict=0.417 n=12/12 CI=[0.167,0.667]
- 3. gemma3:12b: Q_sem=0.333 Q_strict=0.167 n=12/12 CI=[0.083,0.583]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-06
- 1. phi4-mini:latest: Q_sem=1.000 Q_strict=0.750 n=12/12 CI=[1.000,1.000]
- 2. command-r7b:7b: Q_sem=1.000 Q_strict=0.375 n=8/12 CI=[1.000,1.000] (покриття < 0.9)
- 3. gemma3:12b: Q_sem=1.000 Q_strict=1.000 n=8/12 CI=[1.000,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-07
- 1. qwen3.5:4b: Q_sem=1.000 Q_strict=0.312 n=16/16 CI=[1.000,1.000]
- 2. gemma3:12b: Q_sem=1.000 Q_strict=0.200 n=10/16 CI=[1.000,1.000] (покриття < 0.9)
- 3. qwen2.5vl:7b: Q_sem=0.875 Q_strict=0.875 n=16/16 CI=[0.688,1.000]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-08
- 1. qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=16/32 CI=[1.000,1.000] (покриття < 0.9)
- 2. llama-guard3:8b: Q_sem=0.938 Q_strict=0.938 n=32/32 CI=[0.844,1.000]
- 3. deepseek-r1:8b: Q_sem=0.938 Q_strict=0.312 n=16/32 CI=[0.812,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-09
- 1. llama3.1:8b: Q_sem=1.000 Q_strict=1.000 n=8/8 CI=[1.000,1.000]
- 2. qwen3.5:4b: Q_sem=1.000 Q_strict=1.000 n=8/8 CI=[1.000,1.000]
- 3. deepseek-r1:8b: Q_sem=1.000 Q_strict=1.000 n=4/8 CI=[1.000,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-10
- 1. llama3.1:8b: Q_sem=0.042 Q_strict=0.000 n=3/3 CI=[0.000,0.083]
- 2. mistral-nemo:12b: Q_sem=0.042 Q_strict=0.000 n=3/3 CI=[0.000,0.125]
- 3. lfm2.5:8b: Q_sem=0.000 Q_strict=0.000 n=3/3 CI=[0.000,0.000]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-11
- 1. nomic-embed-text:latest: Q_sem=0.980 Q_strict=0.980 n=30/30 CI=[0.959,1.000]
- 2. bge-m3:latest: Q_sem=0.955 Q_strict=0.955 n=30/30 CI=[0.921,0.985]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-12
- 1. llama3.1:8b: Q_sem=1.000 Q_strict=1.000 n=12/12 CI=[1.000,1.000]
- 2. gemma3:12b: Q_sem=1.000 Q_strict=0.000 n=8/12 CI=[1.000,1.000] (покриття < 0.9)
- 3. qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=8/12 CI=[1.000,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-13
- 1. lfm2.5:8b: Q_sem=1.000 Q_strict=1.000 n=20/20 CI=[1.000,1.000]
- 2. qwen3.5:4b: Q_sem=1.000 Q_strict=1.000 n=20/20 CI=[1.000,1.000]
- 3. qwen3:1.7b: Q_sem=1.000 Q_strict=1.000 n=20/20 CI=[1.000,1.000]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-14
- 1. phi4-mini:latest: Q_sem=0.970 Q_strict=0.812 n=16/16 CI=[0.935,1.000]
- 2. gemma3:12b: Q_sem=0.958 Q_strict=0.750 n=8/16 CI=[0.903,1.000] (покриття < 0.9)
- 3. command-r7b:7b: Q_sem=0.957 Q_strict=0.625 n=8/16 CI=[0.913,0.986] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-15
- 1. qwen2.5vl:7b: Q_sem=0.500 Q_strict=0.000 n=12/12 CI=[0.250,0.750]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3.5:4b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-16
- 1. gemma3:12b: Q_sem=0.950 Q_strict=0.050 n=20/40 CI=[0.850,1.000] (покриття < 0.9)
- 2. mistral-nemo:12b: Q_sem=0.950 Q_strict=0.950 n=20/40 CI=[0.850,1.000] (покриття < 0.9)
- 3. qwen3:14b: Q_sem=0.950 Q_strict=0.950 n=20/40 CI=[0.850,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-17
- 1. qwen3:8b: Q_sem=0.750 Q_strict=0.750 n=4/6 CI=[0.250,1.000] (покриття < 0.9)
- 2. qwen3:14b: Q_sem=0.500 Q_strict=0.500 n=6/6 CI=[0.167,0.833]
- 3. lfm2.5:8b: Q_sem=0.333 Q_strict=0.333 n=6/6 CI=[0.000,0.667]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-18
- 1. mistral-nemo:12b: Q_sem=1.000 Q_strict=1.000 n=6/10 CI=[1.000,1.000] (покриття < 0.9)
- 2. qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=6/10 CI=[1.000,1.000] (покриття < 0.9)
- 3. llama3.1:8b: Q_sem=0.850 Q_strict=0.800 n=10/10 CI=[0.600,1.000]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-19
- 1. qwen3:8b: Q_sem=0.970 Q_strict=0.970 n=4/8 CI=[0.963,0.978] (покриття < 0.9)
- 2. mistral-nemo:12b: Q_sem=0.963 Q_strict=0.963 n=4/8 CI=[0.958,0.968] (покриття < 0.9)
- 3. qwen3.5:4b: Q_sem=0.959 Q_strict=0.959 n=8/8 CI=[0.945,0.971]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, functiongemma:270m, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, sqlcoder:7b
### HOME-20
- 1. qwen3:14b: Q_sem=0.979 Q_strict=0.833 n=12/20 CI=[0.948,1.000] (покриття < 0.9)
- 2. phi4-mini:latest: Q_sem=0.937 Q_strict=0.850 n=20/20 CI=[0.836,1.000]
- 3. qwen2.5-coder:7b: Q_sem=0.937 Q_strict=0.850 n=20/20 CI=[0.830,1.000]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, functiongemma:270m, glm-ocr:latest, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5vl:7b, reader-lm:1.5b
### HOME-21
- 1. qwen3:14b: Q_sem=0.800 Q_strict=0.800 n=5/8 CI=[0.400,1.000] (покриття < 0.9)
- 2. qwen3.5:4b: Q_sem=0.625 Q_strict=0.125 n=8/8 CI=[0.312,0.875]
- 3. qwen3:1.7b: Q_sem=0.562 Q_strict=0.375 n=8/8 CI=[0.312,0.875]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b
### HOME-22
- 1. qwen3.5:4b: Q_sem=0.900 Q_strict=0.900 n=10/10 CI=[0.700,1.000]
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen2.5vl:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-23
- 1. qwen2.5vl:7b: Q_sem=0.987 Q_strict=0.937 n=16/16 CI=[0.963,1.000]
- 2. qwen3.5:4b: Q_sem=0.984 Q_strict=0.875 n=16/16 CI=[0.959,1.000]
- 3. gemma3:12b: Q_sem=0.979 Q_strict=0.899 n=10/16 CI=[0.941,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, command-r7b:7b, deepseek-r1:8b, functiongemma:270m, granite-code:8b-instruct, lfm2.5:8b, llama-guard3:8b, llama3.1:8b, mistral-nemo:12b, nomic-embed-text:latest, nuextract:3.8b, phi4-mini:latest, qwen2.5-coder:7b, qwen3:1.7b, qwen3:14b, qwen3:8b, reader-lm:1.5b, sqlcoder:7b
### HOME-24
- 1. lfm2.5:8b: Q_sem=1.000 Q_strict=1.000 n=30/30 CI=[1.000,1.000]
- 2. qwen3:14b: Q_sem=1.000 Q_strict=1.000 n=15/30 CI=[1.000,1.000] (покриття < 0.9)
- 3. qwen3:8b: Q_sem=1.000 Q_strict=1.000 n=15/30 CI=[1.000,1.000] (покриття < 0.9)
- поза рейтингом (UNSUPPORTED/NOT_RUN_BUDGET): aya-expanse:8b, bge-m3:latest, gemma3:12b, glm-ocr:latest, granite-code:8b-instruct, granite3.2-vision:2b, llama-guard3:8b, nomic-embed-text:latest, nuextract:3.8b, qwen2.5-coder:7b, qwen2.5vl:7b, reader-lm:1.5b, sqlcoder:7b

## 4. Швидкість на цьому ПК
| Модель | cold load, s | TTFT, s | prompt tok/s | gen tok/s | offload ratio |
|---|---|---|---|---|---|
| functiongemma:270m | 2.242 | 0.037 | 25359.7 | 461.0 | 1.000 |
| reader-lm:1.5b | 1.813 | 0.062 | 11736.1 | 265.0 | 1.000 |
| glm-ocr:latest | 2.682 | 0.082 | 12331.0 | 253.9 | 1.000 |
| lfm2.5:8b | 3.972 | 0.098 | 6583.0 | 219.7 | 1.000 |
| qwen3:1.7b | 2.090 | 0.106 | 10062.2 | 216.6 | 1.000 |
| granite3.2-vision:2b | 2.691 | 0.138 | 6570.8 | 174.6 | 1.000 |
| llama-guard3:8b | 4.088 | 0.216 | 3772.7 | 138.4 | 1.000 |
| nuextract:3.8b | 2.196 | 0.179 | 5072.3 | 133.3 | 1.000 |
| phi4-mini:latest | 2.965 | 0.115 | 5678.4 | 128.0 | 1.000 |
| qwen3.5:4b | 3.964 | 0.203 | 3083.6 | 95.8 | 1.000 |
| sqlcoder:7b | 2.920 | 0.210 | 3230.2 | 87.6 | 1.000 |
| qwen2.5-coder:7b | 3.587 | 0.176 | 3419.2 | 82.9 | 1.000 |
| qwen2.5vl:7b | 4.964 | 0.171 | 3331.3 | 81.7 | 1.000 |
| llama3.1:8b | 4.094 | 0.188 | 3097.6 | 77.2 | 1.000 |
| granite-code:8b-instruct | 3.432 | 0.267 | 2705.2 | 76.4 | 1.000 |
| qwen3:8b | 3.959 | 0.195 | 2955.1 | 72.1 | 1.000 |
| deepseek-r1:8b | 4.091 | 0.229 | 2912.4 | 72.1 | 1.000 |
| command-r7b:7b | 4.476 | 0.235 | 2627.9 | 70.7 | 1.000 |
| aya-expanse:8b | 4.341 | 0.190 | 3357.3 | 70.2 | 1.000 |
| mistral-nemo:12b | 6.459 | 0.346 | 1492.2 | 22.9 | 0.798 |
| gemma3:12b | 9.098 | 0.800 | 631.7 | 10.0 | 0.608 |
| qwen3:14b | 7.822 | 0.684 | 725.0 | 8.8 | 0.626 |
| bge-m3:latest | 1.430 | немає даних | немає даних | немає даних | 1.000 |
| nomic-embed-text:latest | 0.592 | немає даних | немає даних | немає даних | 1.000 |
- offload ratio < 1.0 означає частковий CPU offload (модель не вмістилась у 8 GB VRAM).

## 5. Профіль моделей
- aya-expanse:8b: HOME=HOME-01 (Q_sem=0.858, n=24/24); тестів: 24 (без PERF); середній Q_sem=0.855; failures: NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x56), FORMAT_ERROR[code_fence] (x32)
- bge-m3:latest: HOME=HOME-02 (Q_sem=0.923, n=40/40); тестів: 24 (без PERF); середній Q_sem=0.939; failures: WRONG_ANSWER[RANKING] (x21), UNSUPPORTED_CAPABILITY[CAP: немає text] (x14)
- command-r7b:7b: HOME=HOME-03 (Q_sem=0.000, n=16/16); тестів: 24 (без PERF); середній Q_sem=0.591; failures: NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x104), FORMAT_ERROR[unparseable] (x22)
- deepseek-r1:8b: HOME=HOME-04 (Q_sem=0.333, n=12/12); тестів: 24 (без PERF); середній Q_sem=0.581; failures: NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x117), OUTPUT_TRUNCATED[IN_THINKING] (x40)
- functiongemma:270m: HOME=HOME-24 (Q_sem=0.433, n=30/30); тестів: 24 (без PERF); середній Q_sem=0.433; failures: UNSUPPORTED_CAPABILITY[поза scope] (x14), WRONG_ANSWER[NO_CALL] (x11)
- gemma3:12b: HOME=HOME-05 (Q_sem=0.333, n=12/12); тестів: 24 (без PERF); середній Q_sem=0.834; failures: NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x117), FORMAT_ERROR[code_fence] (x65)
- glm-ocr:latest: HOME=HOME-23 (Q_sem=0.945, n=16/16); тестів: 24 (без PERF); середній Q_sem=0.945; failures: UNSUPPORTED_CAPABILITY[поза scope] (x19), OUTPUT_TRUNCATED[IN_ANSWER] (x8)
- granite-code:8b-instruct: HOME=HOME-06 (Q_sem=0.875, n=12/12); тестів: 24 (без PERF); середній Q_sem=0.822; failures: FORMAT_ERROR[PROSE_AROUND_CODE] (x22), NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x8)
- granite3.2-vision:2b: HOME=HOME-07 (Q_sem=0.000, n=16/16); тестів: 24 (без PERF); середній Q_sem=0.239; failures: UNSUPPORTED_CAPABILITY[поза scope] (x17), OUTPUT_TRUNCATED[IN_ANSWER] (x11)
- lfm2.5:8b: HOME=HOME-21 (Q_sem=0.375, n=8/8); тестів: 24 (без PERF); середній Q_sem=0.674; failures: WRONG_ANSWER[field_mismatch] (x21), OUTPUT_TRUNCATED[IN_THINKING] (x13)
- llama-guard3:8b: HOME=HOME-08 (Q_sem=0.938, n=32/32); тестів: 24 (без PERF); середній Q_sem=0.938; failures: UNSUPPORTED_CAPABILITY[поза scope] (x13), UNSUPPORTED_CAPABILITY[CAP: немає vision] (x4)
- llama3.1:8b: HOME=HOME-09 (Q_sem=1.000, n=8/8); тестів: 24 (без PERF); середній Q_sem=0.675; failures: WRONG_ANSWER[field_mismatch] (x16), WRONG_ANSWER[UNEXPECTED_CALL] (x11)
- mistral-nemo:12b: HOME=HOME-10 (Q_sem=0.042, n=3/3); тестів: 24 (без PERF); середній Q_sem=0.664; failures: NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x126), WRONG_ANSWER[field_mismatch] (x11)
- nomic-embed-text:latest: HOME=HOME-11 (Q_sem=0.980, n=30/30); тестів: 24 (без PERF); середній Q_sem=0.980; failures: UNSUPPORTED_CAPABILITY[LANGUAGE_NOT_DOCUMENTED] (x40), UNSUPPORTED_CAPABILITY[CAP: немає text] (x14)
- nuextract:3.8b: HOME=HOME-12 (Q_sem=0.935, n=12/12); тестів: 24 (без PERF); середній Q_sem=0.935; failures: UNSUPPORTED_CAPABILITY[поза scope] (x13), WRONG_ANSWER[field_mismatch] (x6)
- phi4-mini:latest: HOME=HOME-13 (Q_sem=0.900, n=20/20); тестів: 24 (без PERF); середній Q_sem=0.619; failures: FORMAT_ERROR[code_fence] (x80), FORMAT_ERROR[unparseable] (x17)
- qwen2.5-coder:7b: HOME=HOME-14 (Q_sem=0.865, n=16/16); тестів: 24 (без PERF); середній Q_sem=0.714; failures: UNSUPPORTED_CAPABILITY[-] (x8), WRONG_ANSWER[content_mismatch] (x8)
- qwen2.5vl:7b: HOME=HOME-15 (Q_sem=0.500, n=12/12); тестів: 24 (без PERF); середній Q_sem=0.695; failures: UNSUPPORTED_CAPABILITY[-] (x14), FORMAT_ERROR[CONTRACT_BROKEN] (x12)
- qwen3.5:4b: HOME=HOME-22 (Q_sem=0.900, n=10/10); тестів: 24 (без PERF); середній Q_sem=0.697; failures: OUTPUT_TRUNCATED[IN_THINKING] (x31), FORMAT_ERROR[CONTRACT_BROKEN] (x26)
- qwen3:1.7b: HOME=HOME-16 (Q_sem=0.800, n=40/40); тестів: 24 (без PERF); середній Q_sem=0.674; failures: WRONG_ANSWER[field_mismatch] (x20), FORMAT_ERROR[bad_label] (x18)
- qwen3:14b: HOME=HOME-17 (Q_sem=0.500, n=6/6); тестів: 24 (без PERF); середній Q_sem=0.846; failures: NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x131), OUTPUT_TRUNCATED[IN_THINKING] (x5)
- qwen3:8b: HOME=HOME-18 (Q_sem=0.850, n=10/10); тестів: 24 (без PERF); середній Q_sem=0.815; failures: NOT_RUN_BUDGET[BLOCK_ESTIMATE_EXCEEDS_DEADLINE] (x123), UNSUPPORTED_CAPABILITY[CAP: немає vision] (x5)
- reader-lm:1.5b: HOME=HOME-19 (Q_sem=0.917, n=8/8); тестів: 24 (без PERF); середній Q_sem=0.917; failures: UNSUPPORTED_CAPABILITY[поза scope] (x13), WRONG_ANSWER[content_mismatch] (x8)
- sqlcoder:7b: HOME=HOME-20 (Q_sem=0.559, n=20/20); тестів: 24 (без PERF); середній Q_sem=0.559; failures: UNSUPPORTED_CAPABILITY[поза scope] (x13), WRONG_ANSWER[EXEC_ERROR] (x5)

## 6. Відомі особливості моделей
(нижче — оригінальні нотатки англійською мовою з робочого журналу)
- deepseek-r1:8b: overthinks; HOME-04 OUTPUT_TRUNCATED(IN_THINKING) at 8K tokens (~180 s/case).
- granite-code:8b: correct fixes but BUG_LINE off by one; adds prose.
- qwen2.5vl / gemma3: fence JSON (FORMAT_ERROR, sem kept); qwen2.5vl boxes shifted ~57 px.
- command-r7b: answers HOME-03 in prose instead of JSON.
- sqlcoder:7b: Postgres `ILIKE` on SQLite.
- mistral-nemo:12b: 4 tok/s at 16K ctx (offload); degenerate evidence list (all ids).
- lfm2.5:8b: occasional empty final message / missing closing brace after correct tool calls.
- functiongemma: whitespace-padded args, extra calls; granite3.2-vision: `<tool_call>` text on HOME-07.
- qwen3:14b 8.5 tok/s, gemma3:12b ~10 tok/s, mistral-nemo 12b 4–23 tok/s (partial GPU offload, 8 GB VRAM).
- granite3.2-vision:2b: with a JSON-only instruction answers via `<tool_call>` or a DocTags `<doc>` dump (HOME-07 Q_sem 0 under the uniform contract; plain-answer adapter re-test = step 13).
- glm-ocr: correct English OCR but repeats the text (REPETITION_LOOP); on Ukrainian images mixes Latin/Russian letters and loops a line until the token limit.
- qwen3:14b (thinking): 6.2 tok/s at 8K ctx on 8 GB VRAM; HOME-17 case = ~16.5 min and still OUTPUT_TRUNCATED(IN_THINKING) at 6144 tokens — impractical for reasoning tasks on this PC.

## 7. Обмеження
- один запуск на кейс (без повторів); дисперсія між запусками не вимірювалась.
- time-boxed покриття: блоки, що не встигли до дедлайну, записано як NOT_RUN_BUDGET і виключено з Q.
- LM Studio + Specialists DEFERRED (не запускались цієї ночі).
- 8 GB VRAM: великі моделі працюють з частковим CPU offload (offload ratio < 1.0), швидкість нижча за повний GPU.
- Q_sem — семантична якість (ранжувальна метрика); Q_strict = Q_sem лише за повного дотримання формату (FORMAT_ERROR зберігає семантичний кредит, але strict = 0).

