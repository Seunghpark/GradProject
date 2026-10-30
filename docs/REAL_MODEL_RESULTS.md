# Logistic-baseline pilot results (preserved earlier experiment)

Current deep-learning extension: see DEEP_LEARNING_RESULTS.md. The installed model is now the genuine MLP; this file preserves the earlier logistic result.

Observed on 2026-10-28 (Asia/Seoul). This is a local graduation-project pilot, not a claim of general League of Legends prediction accuracy.

## What was collected

Live ACCOUNT-V1 and MATCH-V5 responses were retrieved by the user's running FastAPI backend. Collection began with the user-entered Molybdite#KR1 on KR and expanded to five participants observed in those ranked games. The same /api/analysis endpoint retained allowlisted routing, backend-only credentials, caching, conservative pacing and Retry-After cooldown. The agent shell could not resolve Riot hosts, so direct CLI collection was not used for this snapshot.

The local cache contained 116 distinct match details and 104 complete eligible match/timeline pairs. The 12 remaining details were not included in the training export. After ranked/map/duration/participant/frame checks, the exported dataset has 104 unique genuine matches, each with source=riot. There are no duplicate IDs in this export and no additional records rejected by the trainer. These are different counts from analysis rows: the same match can appear in multiple players' views.

All 104 exported matches are KR ranked solo/duo (queue 420, map 11). They contain 58 blue wins and 46 red wins, on patches 16.20.824.8524 and 16.21.829.8620. Match start times span 2026-10-20 07:44:29 UTC through 2026-10-28 04:42:16 UTC. This is a connected convenience sample with overlapping players, not a representative population sample.

## Method and observed evaluation

Features are blue-minus-red gold, XP, CS, kills, towers and dragons from the latest complete timeline frame in [540000, 600000] milliseconds. The actual selected frames in this snapshot are 540.088-540.308 seconds: about minute 9. The next nominal minute-10 frame falls after the strict cutoff. Final statistics and future events do not enter prediction inputs. Outcomes supply training labels only.

One blue-side row per unique match is ordered chronologically. The first 83 matches train the StandardScaler and logistic regression; the later 21 are held out. Training contains 48 blue wins/35 red wins; holdout contains 10 blue wins/11 red wins. The latest training match starts 2026-10-26 02:46:23 UTC; the earliest held-out match starts 2026-10-26 03:28:18 UTC. Match IDs are disjoint across partitions. No holdout tuning was performed.

Measured on the same 21 held-out matches:

- Logistic regression: 12/21 correct, accuracy 57.14%, ROC-AUC 0.6091, Brier score 0.26356.
- Constant training-prior baseline: blue-win probability 48/83 (0.57831), 10/21 correct, accuracy 47.62%, ROC-AUC 0.5000, Brier score 0.25986.

Higher accuracy amounts to two additional correct decisions in a tiny holdout. Lower Brier is better, and the model is slightly WORSE than the baseline on that metric. This pilot therefore does not demonstrate superior probability quality, calibration, broad generalization or player improvement. Report both metrics and the baseline, including the weak result. There is no independent external validation or uncertainty study.

## Local artifacts and reproduction

The ignored backend/data/riot_matches.jsonl preserves the collected raw match/timeline pairs. Its SHA-256 is be988d94be1853b30b35ca6e3f8aaf4305be9a275a353666829e099bfe62368c. The saved model and complete evaluation are backend/data/riot_model.json and backend/data/riot_model_evaluation.json. The logistic artifact was previously installed at backend/data/model.json; that serving path now holds the MLP. The preserved riot_model.json retains the baseline. The previous fictional model is retained at backend/data/synthetic_model.json. Credentials, raw datasets and generated models are ignored by Git.

From the project root, using this exact saved dataset:

```powershell
.venv/Scripts/python.exe backend/scripts/train_model.py --input backend/data/riot_matches.jsonl --output backend/data/riot_model.json
```

The report includes partition match IDs, SHA, time ranges, class counts, patches, queue and library versions. This run used numpy 2.5.4 and scikit-learn 1.9.1. An independent recomputation from the saved JSON coefficients and raw held-out records reproduced all reported metrics. Recollecting recent API history later produces a different dataset; it cannot reproduce this exact snapshot unless these private raw records are retained.

A fresh source checkout does not include the genuine raw dataset or model and setup creates a labeled synthetic model. Do not present that fresh-checkout demo as this real-data evaluation. Preserve the private research snapshot separately if required by the university, without including credentials or unnecessarily publishing player identifiers.

## Serving and interpretation

The running browser has displayed real Molybdite#KR1 matches, non-null genuine-model probabilities and the 83/21 evaluation. A selected player's team receives blue probability or its complement for red. Individual displayed matches can belong to training data; they illustrate inference and are not additional validation examples. Only the separate held-out evaluation supports the metrics above.

The app remains historical analysis with descriptive post-match review. Logistic regression is machine learning, not deep learning. No experiment has established improved player win rate, causal advice, survey results or the original draft's unsupported 1,000-match/6.7% claims. The user confirmed deep learning is mandatory; see the implemented extension and submission requirements.
