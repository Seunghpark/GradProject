# Historical match-prediction model card

## Scope

Estimate eventual blue-team victory from an early snapshot of a completed
ranked Summoner's Rift match. Red-team displays use the complementary value.
This is retrospective analysis, not a pre-match forecast, skill-tier estimate,
live coach or causal recommendation.

## Implementation and inputs

The active feedforward MLP has six standardized inputs, ReLU hidden layers
16–8–4 and one sigmoid output: 6→16→8→4→1, 289 parameters. Training uses
scikit-learn `MLPClassifier`; serving validates plain JSON parameters and uses a
standard-library forward pass. No executable pickle is loaded.

Fixed training settings: L-BFGS, alpha=1, random_state=42, max_iter=2000,
max_fun=20000, tol=1e-6, no early stopping. The architecture/settings were not
swept to maximize the observed holdout. Original training converged at 1062
iterations. Train-only scaling is shared with the logistic comparison.

Features are blue-minus-red gold, XP, lane+jungle CS, champion kills, towers and
dragons through the latest complete participant frame in [540000,600000] ms.
Actual original frames are approximately 540.09 seconds. Final KDA, damage,
gold, future events and winner labels do not enter these historical inputs.
Winner is used as the supervised target only. Full-match review is a separate
retrospective calculation.

Eligibility requires map 11, ranked queue 420 or 440, duration over ten minutes,
ten unique participants, five per team, matching match/timeline IDs and a
complete early frame. Missing/ineligible data produces no prediction.

## Original experiment

104 unique genuine KR ranked games, October 20–28, 2026, patches 16.20/16.21.
Collection began from one player and observed participants, so repeated players
and selection bias limit independence. Chronological split: 83 training games
(48 blue/35 red wins), 21 later holdout games (10 blue/11 red wins). IDs do not
overlap, and training games finish before evaluation games begin.

- MLP holdout: 10/21 correct, accuracy 47.62%, AUC 0.490909, Brier 0.372683.
- Logistic holdout: 12/21, 57.14%, 0.609091, 0.263561.
- Constant 48/83 training prior: 10/21, 47.62%, 0.5, 0.259862.
- Exploratory RF: 14/21, 66.67%, 0.590909, 0.260681; not installed as serving model.

MLP training accuracy is 95.18%, an in-sample diagnostic consistent with
overfitting when compared with the weak holdout. The holdout had already been
viewed for the logistic experiment; subsequent comparisons remain exploratory.
RF settings were selected after that holdout had been viewed. No XGBoost result
was produced in this environment. The lost historical 1,000-game/79% result is
not recovered or reproduced evidence.

## Separate later-period audit

Before extra collection and performance calculation, model copies/hashes and
108 prior/reviewed game exclusions were fixed. A 180-game collection snapshot
excluded those 108 games and 37 games predating model creation, leaving 35 later
eligible games: 15 blue/20 red wins. Sampling used other participants from one
seed roster; recruitment expanded from three to nine players before calculating
performance because the first eight eligible games were below the minimum 20.

Results dated October 30, 2026, 18:12 KST:

- Unchanged MLP: 20/35, accuracy 57.14%, AUC 0.67, Brier 0.319481.
- Unchanged logistic: 28/35, 80.00%, 0.873333, 0.168850.
- Constant original training prior: 15/35, 42.86%, 0.5, 0.267321.

No model was retrained or replaced. The audit is retrospective convenience
sampling with a retrospectively chosen protocol, not independent external
validation. It includes repeated-player relationships. Different sample scores
do not establish an improved model; MLP Brier remains worse than both baselines.

## Artifact identity and safe inference

- Original private `riot_matches.jsonl` SHA-256:
  `be988d94be1853b30b35ca6e3f8aaf4305be9a275a353666829e099bfe62368c`.
- Active `backend/data/model.json` SHA-256:
  `9a64650a4dade3b14c0370c999df8573b36da524cd6a413dee9b492a6cee017e`.
- Logistic `backend/data/riot_model.json` SHA-256:
  `95e167e41f93f030c49a3ec89d0096da1f86fd7ca0cb074d5680e0981de973e1`.

Serving checks finite/bounded values, dimensions, activations, scaling and
source compatibility. A genuine-only model refuses fictional matches. Cache
versions include artifact content. Missing/invalid artifacts produce an
unavailable result. Declared provenance is checked against saved collection
evidence; a label alone is not independent authentication.

Published model/aggregate JSON supports inference and inspection. Exact
retraining requires excluded private raw records and the original protocol.
Use new explicit output paths for further studies; preserve original datasets,
weights and viewed-holdout results. The collector's default JSONL output must
not be used to extend the frozen research snapshot.

## Limits and supporting documentation

No neural superiority, calibration, causal advice, player improvement,
low-elo subgroup performance or public-production readiness is established.
Current rank/mastery is not historical training input. Full-game review metrics
and tip priorities do not enter the early team model.

See [validation](VALIDATION.md), [temporal models](TEMPORAL_MODELS.md),
[tip methods](TIPS_ENGINE.md), and the final report for details.
Implementation references: [scikit-learn neural networks](https://scikit-learn.org/stable/modules/neural_networks_supervised.html),
[MLPClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html),
[Riot LoL documentation](https://developer.riotgames.com/docs/lol).
