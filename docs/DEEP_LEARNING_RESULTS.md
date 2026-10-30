# LolAi.gg deep-learning experiment

Date: 2026-10-28, Asia/Seoul. The user confirmed deep learning is mandatory and the final deadline is 2026-10-30 23:59 (Korean time assumed). Earlier uploaded report/presentation files and screenshot upload entries are samples, not evidence of completed work or submission.

## Implemented neural network

A feedforward multilayer perceptron has six standardized team-difference inputs, three hidden layers of 16, 8 and 4 neurons with ReLU activations, and one sigmoid output for blue-team victory: 6 -> 16 -> 8 -> 4 -> 1. It learns 289 weights/biases. Training uses scikit-learn MLPClassifier, L-BFGS optimization of regularized log loss, alpha=1, random_state=42, max_iter=2000, max_fun=20000, tol=1e-6 and no early stopping. No new dependency or GPU is required. Hidden layers and nonlinear activations make this an actual trained deep feedforward network; logistic regression remains a comparison baseline.

The fixed architecture and settings were chosen before running this comparison. They were not tuned to maximize these holdout results. Training converged after 1062 optimizer iterations, without a convergence warning. Parameters/scaler are saved as plain JSON; production inference performs the forward pass using Python's standard library. No pickle or executable serialized model is loaded.

Implementation reference: [scikit-learn neural network guide](https://scikit-learn.org/stable/modules/neural_networks_supervised.html), [MLPClassifier reference](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html).

## Genuine data and leakage controls

The existing 104 unique authenticated Riot match/timeline pairs remain unchanged. They are KR ranked solo/duo, map 11, spanning 2026-10-20 through 2026-10-28 and patches 16.20/16.21. Collection began with Molybdite#KR1 and five observed participants, so player overlap and selection bias are substantial. Raw data and keys stay outside source control.

The same 83 earlier matches train both neural and logistic models; the same 21 later matches evaluate both. Training has 48 blue wins and 35 red wins; evaluation has 10 blue wins and 11 red wins. StandardScaler fits training data only. Model comparison uses identical features, scaler, IDs and labels. All training matches finish before the first evaluation match starts, and no IDs overlap across partitions.

Features are blue-minus-red gold, XP, CS, kills, towers and dragons through the latest complete frame in the strict 9-to 10-minute window. Actual frames in this snapshot are about 540.09 seconds, because the next frame is slightly after 600 seconds. Final match statistics and future events are excluded from features. Winner labels are used only for supervised training/evaluation. The full-match gold chart and post-match review use later information and are clearly retrospective.

Dataset SHA-256: be988d94be1853b30b35ca6e3f8aaf4305be9a275a353666829e099bfe62368c.

## Measured results

On the same 21 later matches:

- Deep MLP:10/21 correct, accuracy 47.62%, ROC-AUC 0.49091, Brier 0.372683.
- Logistic regression:12/21 correct, accuracy 57.14%, ROC-AUC 0.60909, Brier 0.263561.
- Constant training-prior baseline:10/21 correct, accuracy 47.62%, ROC-AUC 0.50000, Brier 0.259862. Its fixed blue-win probability is 48/83.

Training diagnostics for the neural network:79/83 correct (95.18%), Brier 0.034691, ROC-AUC 0.995833. These are in-sample diagnostics, NOT validation results. The large train/evaluation gap is consistent with overfitting. The neural network does not beat the baselines on this sample; its probability error is worse. This is a functioning deep-learning implementation with a negative pilot result, not evidence of improved or calibrated predictive quality.

The 21-match holdout had already been inspected for the earlier logistic baseline. This extension reuses it for an explicitly exploratory comparison, not a fresh independent test. No model was selected for superior holdout performance, and no architecture/seed/regularization sweep was run. More diverse data and a genuinely untouched evaluation set are needed for stronger conclusions. Neither user improvement nor causal coaching nor survey outcomes were studied.

An independent standard-library forward pass from saved parameters reproduced all evaluation metrics within 1e-12. It also checked the dataset hash, partitions, scaler,289 parameters, team orientation and temporal completion boundary. No refitting was used for this verification.

## Artifacts and reproduction

Private ignored local artifacts:

- backend/data/riot_matches.jsonl: original genuine pairs.
- backend/data/riot_mlp_model.json and riot_mlp_model_evaluation.json: neural parameters and full report.
- backend/data/model.json: installed genuine MLP for serving.
- backend/data/riot_model.json and riot_model_evaluation.json: preserved earlier logistic model/result.

Reproduce from the project root using the exact saved dataset:

```powershell
.venv/Scripts/python.exe backend/scripts/train_model.py --input backend/data/riot_matches.jsonl --output backend/data/riot_mlp_model.json --algorithm mlp
```

The report records training diagnostics separately from evaluation, plus architecture, optimizer, iterations/convergence, library versions, input hash, patch/queue/date/class coverage and all partition IDs. The same CLI defaults to logistic regression when --algorithm is omitted. A fresh setup creates a clearly labeled synthetic MLP if no model exists; it cannot reproduce these genuine-game metrics without the private snapshot.

## Tests and serving status

MLP-specific tests check exported forward-pass parity with scikit-learn over 120 fictional fixtures, red complement, identical neural/logistic partitions and preprocessing, baseline equality, malformed dimensions/activations, nonfinite/oversized numbers, intermediate numerical overflow and real/synthetic source guards. The neural model preserves the artifact-content cache version so stale analyses cannot cross model versions.

The 17 model tests and six subtests passed after final integration in 4.99 seconds. On October 29, the user supplied normal Cursor terminal evidence: 44 passed, 1 warning, 6 subtests passed in 40.93s. The warning is Starlette's httpx/httpx2 deprecation notice. The server was restarted, and a fresh browser model screen displayed the trained Deep MLP with 289 parameters and the 83/21 split. A live Molybdite#KR1 lookup returned ten genuine matches with neural estimates. The downloaded JSON contained ten finite probabilities within [0,1], model evaluation exactly equal to the installed artifact report, and no Riot key-shaped value. These checks validate current application execution and export; they do not establish stronger prediction quality. See QA_RESULTS.md for evidence and limits. The prior 39-test result belongs to the earlier logistic-only build.
