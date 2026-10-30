# Historical probability timeline and input sensitivity

Implemented on 2026-10-30. These additions extend the historical research demo; they do not establish a useful coaching service or improved predictive quality.

## What now works

- `prediction_review.py` reports the actual timestamp of the original early snapshot, six training-mean input sensitivity comparisons, and observed champion kill / tower / inhibitor / major-monster events.
- A sensitivity difference is the current player's team probability minus the probability obtained when **one blue-minus-red input** is replaced by its training-set mean. Other inputs stay fixed. Differences do not sum to a causal explanation and are not SHAP values or recommendations. Correlated inputs can make the substituted combination unrealistic.
- `temporal_model.py` serves a separately trained MLP at each supported target minute. It never applies the original minute-10 model to every minute.
- `train_timeline_models.py` creates a separate `backend/data/timeline_models.json` artifact. It preserves `backend/data/model.json` and its original reported result.
- Synthetic/real source guards, malformed-artifact checks, missing-frame checks, and blue/red probability complements also apply to temporal predictions.

## Fixed experiment

The new artifact uses the existing 104-game KR ranked dataset, its exact input SHA, and the **unchanged global 83-game training / 21-game holdout assignment** from the saved original model. A game cannot move between partitions at a different minute. All training games ended before the first holdout game began. Duplicate IDs are excluded.

Each target selects the latest complete frame in the inclusive one-minute interval ending at that target. The actual frames in this dataset are about one minute before their target because the next recorded frame arrives just after the cutoff. For example, target 5 uses approximately 240.010–240.207 seconds; target 10 uses 540.088–540.308 seconds; target 15 uses 840.193–840.400 seconds. The graph must position points at the **actual recorded frame time**, not imply exact-minute observations.

Each model uses six blue-minus-red inputs: gold, XP, CS, kills, towers, and dragons. It has the same 6→16→8→4→1 architecture, ReLU hidden activations, sigmoid output, and 289 parameters. StandardScaler is fitted independently to that minute's eligible training games only. MLP settings are fixed: L-BFGS, alpha 1, seed 42, max_iter 2000, max_fun 20000, tolerance 1e-6, early_stopping false. Logistic regression and a constant training-prior baseline use the same games at each target. No hyperparameter search or best-minute selection was performed. All 11 training fits completed without convergence warnings.

Minimums are 60 training games, 20 holdout games, and both outcomes in training. Targets 5–15 met those requirements. Targets 16–20 were skipped because only 19, 19, 19, 19, and 17 holdout games respectively remained eligible. No interpolation or extrapolation supplies missing targets.

## All temporal results

These are exploratory results on the **already viewed holdout**, not independent validation. Later targets have different eligible populations because games must still be in progress. Do not compare target scores as though the test population were fixed, choose the best minute after inspecting these scores, or present the largest accuracy as the application's overall accuracy.

For each target below, metrics are blue-label accuracy / ROC-AUC / Brier score. Lower Brier is better.

- Target 5; 83 train, 21 holdout: MLP **0.4762 / 0.5909 / 0.4310**; logistic **0.5238 / 0.5727 / 0.2910**; constant **0.4762 / 0.5000 / 0.2599**.
- Target 6; 83 / 21: MLP **0.5714 / 0.6545 / 0.3072**; logistic **0.3810 / 0.6364 / 0.3129**; constant **0.4762 / 0.5000 / 0.2599**.
- Target 7; 83 / 21: MLP **0.4286 / 0.5182 / 0.4409**; logistic **0.3810 / 0.6091 / 0.2871**; constant **0.4762 / 0.5000 / 0.2599**.
- Target 8; 83 / 21: MLP **0.5714 / 0.6182 / 0.2793**; logistic **0.5714 / 0.6455 / 0.2618**; constant **0.4762 / 0.5000 / 0.2599**.
- Target 9; 83 / 21: MLP **0.6667 / 0.6909 / 0.2720**; logistic **0.5238 / 0.7000 / 0.2675**; constant **0.4762 / 0.5000 / 0.2599**.
- Target 10; 83 / 21: MLP **0.4762 / 0.4909 / 0.3727**; logistic **0.5714 / 0.6091 / 0.2636**; constant **0.4762 / 0.5000 / 0.2599**. This target's weights, scaler, and metrics exactly match the existing active minute-10 artifact.
- Target 11; 82 / 21: MLP **0.6190 / 0.6091 / 0.3371**; logistic **0.6190 / 0.6909 / 0.2341**; constant **0.4762 / 0.5000 / 0.2614**.
- Target 12; 82 / 20: MLP **0.5000 / 0.6100 / 0.4086**; logistic **0.6500 / 0.7100 / 0.2247**; constant **0.5000 / 0.5000 / 0.2573**.
- Target 13; 82 / 20: MLP **0.5500 / 0.4600 / 0.3894**; logistic **0.7000 / 0.7200 / 0.2271**; constant **0.5000 / 0.5000 / 0.2573**.
- Target 14; 82 / 20: MLP **0.6500 / 0.7800 / 0.2411**; logistic **0.7000 / 0.6300 / 0.2378**; constant **0.5000 / 0.5000 / 0.2573**.
- Target 15; 82 / 20: MLP **0.6000 / 0.7300 / 0.3518**; logistic **0.6000 / 0.7800 / 0.2165**; constant **0.5000 / 0.5000 / 0.2573**.

The MLP is worse than logistic regression by Brier score at every target except target 6. It is worse than the constant baseline by Brier score at every target except target 14. These probabilities remain poorly supported for real decisions. Changes between successive points can reflect different model fits as well as changed observations; they do not measure an objective's or fight's causal effect.

## Verification and reproduction

Run the focused tests from the repository root with the installed virtual environment:

```powershell
$env:TEMP=(Resolve-Path '.tmp').Path
$env:TMP=$env:TEMP
.\.venv\Scripts\python.exe -m pytest backend/tests/test_prediction_review.py backend/tests/test_ml.py backend/tests/test_temporal_model.py -q
```

Result: **32 passed, 6 subtests passed** in 5.34 seconds. These cover unchanged default extraction, future/final-data exclusion, input/reference differences, malformed inputs, source guards, complementary team probabilities, train-only scalers, unchanged game splits, missing/short snapshots, temporal metric reproduction, and preservation of the reference artifact. The initial run without workspace TEMP failed due sandbox temporary-directory permissions; the workspace-TEMP run passed.

A separate NumPy matrix-forward calculation reproduced all **227 holdout timepoints** across the 11 genuine models with maximum probability error **1.72e-15**. All saved accuracy, ROC-AUC, and Brier scores matched within 1e-12. These 227 timepoints repeat the same 20–21 games; they are **not 227 independent matches**.

To retrain from the private raw JSONL and saved split:

```powershell
.\.venv\Scripts\python.exe backend/scripts/train_timeline_models.py
```

The script refuses an input SHA that differs from the reference experiment and refuses to overwrite the reference model or dataset. Runtime inference requires the separate temporal artifact but not raw data. No new API calls are needed for this experiment. A package that excludes raw data cannot independently retrain these models.

Artifact: `backend/data/timeline_models.json`, 219,444 bytes; SHA-256 `cde835c0168f4ccda610f16c1f420d1eb5e11d9f3836dd77975f51460507e82b`.

Preserved active model SHA-256: `9a64650a4dade3b14c0370c999df8573b36da524cd6a413dee9b492a6cee017e`.

The original 1,000-game dataset and historical XGBoost result remain unrecovered. No fresh held-out dataset, calibration study, lower-elo ablation, causal feedback evaluation, or user improvement study was performed by these additions.
