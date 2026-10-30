# LolAi.gg historical model card

## Current required deep model

The user confirmed deep learning is mandatory on 2026-10-28. The installed local model is now a genuine three-hidden-layer feedforward network: 6 inputs -> 16 ReLU -> 8 ReLU -> 4 ReLU -> 1 sigmoid, with 289 learned parameters. Training uses the existing scikit-learn MLPClassifier; serving uses bounded plain JSON and a standard-library forward pass. The preserved logistic artifact is a comparison baseline, not the deep model.

Both use the same unchanged 104 genuine matches, 83 earlier training / 21 later evaluation, with train-only scaling. MLP evaluation: accuracy 47.62%, AUC 0.49091, Brier 0.37268; logistic: 57.14%, 0.60909, 0.26356; constant-prior Brier 0.25986. The neural model is worse in this pilot. Neural training accuracy 95.18% is an in-sample diagnostic; its gap from evaluation is consistent with overfitting. The previously viewed holdout is an exploratory comparison, not independent validation.

See [deep-learning results](DEEP_LEARNING_RESULTS.md) for fixed optimizer settings, convergence, safe serving, exact metrics and limitations. The earlier [logistic experiment](REAL_MODEL_RESULTS.md) is preserved. A fresh setup creates a labeled synthetic MLP, not this private genuine snapshot. Earlier uploads are samples per the user and supply no final submission evidence. The confirmed final deadline is October 30 at 23:59; see SUBMISSION_REQUIREMENTS.md.

## Research question

Given observations available by minute 10 of a completed ranked Summoner's Rift match, estimate the eventual probability of a blue-team victory. The UI reverses that probability for a red-team player. This is retrospective analysis, not live coaching, a pre-match forecast, an MMR estimate, or causal advice.

## Data and features

Input JSONL records have `source` (`riot` or `synthetic`), `match` (raw Match-V5 result), and `timeline` (raw Match-V5 timeline). Match IDs must agree. Eligibility requires map 11, queue 420 or 440, duration greater than ten minutes, exactly ten unique participants with five on each team, and a complete participant frame in [540000, 600000] milliseconds. The latest eligible frame is selected. Thus minute 10 can mean the last observation up to one minute earlier; stale snapshots are rejected.

Features are blue-minus-red total gold, total XP, lane plus jungle CS, champion kills, towers destroyed, and dragons killed. Participant/team mappings come from match metadata, not presumed participant numbering. Events are included only through the selected frame timestamp. The building event's `teamId` is its destroyed tower's owner. Final KDA, final gold/damage and winner labels cannot influence feature extraction. Final winner is used only as the supervised target. Unsupported modes, short matches, absent timelines and incomplete snapshots produce no prediction.

## Shared protocol and logistic baseline

Training requires at least 100 eligible unique matches, with at least 60 earlier training and 20 later test records. One blue-side row per match prevents team-perspective leakage. IDs are deduplicated, then records sorted by game start time. The nominal split is 80% train / 20% holdout; ties at the boundary all stay in holdout. Both outcomes must occur in training. StandardScaler fits training rows only. Logistic regression uses C=1, max_iter=2000, random_state=42; no tuning uses holdout data.

The generated `model_evaluation.json` records input SHA-256, eligible/skipped/duplicate counts, train/test match IDs, time ranges, queue and patch coverage, class counts, library versions, accuracy, Brier score and ROC-AUC. The constant baseline uses training-set blue-win prevalence, not test prevalence. AUC is null for single-class holdouts. Results are one temporal holdout, with no external validation or probability-calibration study. The current real collection has player overlap, selection bias, only one platform and two nearby patches. Collect substantially more diverse data than the minimum and obtain independent validation before making generalized claims. Displayed individual matches may overlap training data and must not be counted as extra validation.

## Artifacts and provenance

`backend/data/model.json` contains plain JSON parameters and provenance; serving needs no sklearn or pickle. Set backend `MODEL_PATH` to choose another artifact. Inference refuses source mismatches: a synthetic artifact cannot emit a probability for a Riot match. Cached Riot responses remain `riot`, never synthetic. Provenance labels are declarative, so verify collection origin before research claims. Missing or invalid model files produce an unavailable result.

## Reproduce synthetic fixtures

These commands are for fictional fixtures. They overwrite the default model when no separate --output is supplied; keep the genuine artifact or choose a separate synthetic output path.

From `backend` after installing requirements:

```powershell
..\.venv\Scripts\python.exe scripts/generate_synthetic_training.py --count 300
..\.venv\Scripts\python.exe scripts/train_model.py --input data/synthetic_training.jsonl --output data/synthetic_mlp_model.json --algorithm mlp
..\.venv\Scripts\python.exe -m pytest tests/test_ml.py -q
```

The default seed is 20261026. The generator creates stochastic fictional outcomes from a latent advantage; it tests the pipeline and does not simulate the actual game. All records are explicitly synthetic with fictional IDs and patch labels. The training command prints measured demo metrics and writes the report beside the model. Do not present these as real-game metrics.

For real data, collect completed match and timeline responses using the official API into the same JSONL shape with source `riot`, inspect coverage, and run the identical CLI with `--input data/riot_matches.jsonl --output data/riot_mlp_model.json --algorithm mlp`. Select it using `MODEL_PATH` after reviewing its evaluation. Never relabel fixtures.

## Riot API scope

The application uses historical Match-V5 data and post-match insights. It does not retrieve live hidden information, dictate ongoing-match decisions or expose custom-queue history. Riot recognizes school projects and historical training tools as use cases; that is not blanket approval of every prediction product. Public live deployment requires appropriate Riot access/registration. See the [LoL documentation](https://developer.riotgames.com/docs/lol) and [developer portal documentation](https://developer.riotgames.com/docs/portal).

Neural implementation references: [scikit-learn guide](https://scikit-learn.org/stable/modules/neural_networks_supervised.html) and [MLPClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html). The exact supported neural architecture is validated, including finite weights, positive scaler scales and adjacent dimensions; malformed or overflowing inputs disable inference.
