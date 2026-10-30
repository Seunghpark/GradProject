# LolAi.gg

Historical League of Legends analysis for an SKKU graduation project. React and
TypeScript provide the interface; FastAPI and SQLite handle Riot requests,
stored matches, native analysis and model inference. Program version: **0.6.0**.

## Final deliverables

- [Final report PDF](submission/final_v07_2026-10-30/LolAi_FinalReport_v07.pdf) — 47 pages.
- [Editable report](submission/final_v07_2026-10-30/LolAi_FinalReport_v07.docx).
- [Presentation](submission/final_v07_2026-10-30/소프트웨어학과_박승현(2019310202).pptx) — 18 slides.
- [Clean source and academic package](submission/LolAi_Final_Package_v07_Clean_2026-10-30.zip).

Student: 박승현 (2019310202), 소프트웨어학과 / 소프트웨어융합대학.
Adviser: 한환수. Project: 개인 작품.

## Implemented features

- Riot ID lookup and completed ranked-match history with regional routing,
  caching, paging, partial-data handling and an explicitly fictional demo.
- Ten-player scoreboards, role-opponent comparisons, gold timelines, player
  shares, item/rune/spell information and observed purchase/skill histories.
- Native champion/role/patch/queue aggregates and recent player profiles.
- Explainable post-match review priorities and private practice tracking.
- A three-hidden-layer MLP, logistic/constant baselines, separate temporal
  models and transparent evaluation/sensitivity displays.
- Dated current-rank observations, optional provider-labeled OP.GG archive API
  and YouTube metadata. Riot data and LolAi calculations remain the main path.
- English/Korean switching and JSON analysis export.

This is a local single-user prototype. Descriptive build frequencies and review
prompts are not validated optimal strategies or causal coaching recommendations.
Full feature parity with commercial analytics services is outside this release.

## Run on Windows

Use PowerShell in the project directory. On the existing prepared computer:

```powershell
.\start.cmd
```

Open http://127.0.0.1:8000 and keep the server terminal open. Stop with Ctrl+C.

For a new computer, install Python 3.11 or later, Node.js and pnpm or npm, then
run the existing `setup.ps1` with the machine's permitted PowerShell policy.
It creates `.venv`, installs dependencies and builds the frontend. A clean new
computer installation has not been verified. Do not change global execution
policy just to run this project.

API credentials are optional for the fictional demo. For live lookups, create
`backend/.env` from `backend/.env.example` and set `RIOT_API_KEY` locally.
`YOUTUBE_API_KEY` is optional for video metadata. Never put keys in frontend
variables, Git, screenshots or exported reports. Restart the server after
configuration changes.

The published genuine model intentionally does not estimate fictional matches.
The demo still displays fictional statistics and review examples with explicit
source labels. A missing/invalid model produces an unavailable estimate.

## Demonstration

1. Start the app and inspect the clearly labeled sample demo.
2. With a valid Riot key, look up `Molybdite#KR1`, Korea, using Live Riot API.
3. Inspect a match, native review, complete scoreboard and purchase/skill history.
4. Open Model & evaluation and compare the neural model with its baselines.
5. Switch English/Korean and export the analysis JSON.

Live availability depends on Riot access, request limits and the player's
available history. Current ranks are not retroactively treated as historical
game-time ranks.

## Checks

From a separate project terminal:

```powershell
.\check.cmd
```

Frontend checks/build from `frontend`:

```powershell
node --test tests/resources.test.mjs tests/profile-review.test.mjs tests/i18n.test.mjs tests/research-tools.test.mjs tests/native.test.mjs
pnpm run build
```

Recorded full backend result: **276 passed, one warning, six subtests passed**.
Frontend: **41 tests passed** and TypeScript/Vite build passed. A later restricted
check passed 230 backend tests plus six subtests and repeated the 41 frontend
tests; it is not another full-suite result. See [validation](docs/VALIDATION.md)
and the [full backend receipt](docs/TEST_RESULTS.txt).

## Research results

The original frozen experiment contains 104 genuine KR games, split
chronologically into 83 training and 21 later holdout games. The network is
**6 → 16 → 8 → 4 → 1**, with three ReLU hidden layers and 289 parameters.
Inputs are early team differences in gold, XP, CS, kills, towers and dragons.
The selected complete frame is in the 9–10-minute window; actual original frames
are around nine minutes, not exact 10:00.

Original 21-game holdout:

- MLP: accuracy 47.62%, ROC-AUC 0.490909, Brier 0.372683.
- Logistic: 57.14%, 0.609091, 0.263561.
- Constant training prior: 47.62%, 0.5, 0.259862.
- Exploratory RF: 66.67%, 0.590909, 0.260681; the serving model was not replaced.

A separate retrospective 35-game later-period audit of unchanged models measured
MLP 57.14% / AUC 0.67 / Brier 0.319481 and logistic 80.00% / 0.873333 / 0.168850.
Different samples do not establish model improvement. Neural superiority,
probability calibration and coaching efficacy were not demonstrated.

Read the [model card](docs/MODEL_CARD.md),
[temporal-model methods](docs/TEMPORAL_MODELS.md) and
[own tip formula](docs/TIPS_ENGINE.md) for the protocol and limitations.
The original holdout was already viewed; the later audit is a convenience
sample, not independent external validation. Low-elo validation has no eligible
cohort. Learned player-impact weights, authenticated peer feedback, actual-game
acceptance and public production deployment remain incomplete or unverified.

## Data, reproducibility and contribution

Model parameters and aggregate numerical reports are included. Raw JSONL,
SQLite stores, private notes/rank observations, API keys, certificates, caches
and installed dependencies are excluded. Experiments requiring private raw
records cannot be independently retrained from this public package alone.
`PUBLICATION_MANIFEST.json` lists the current public files and hashes; the
download ZIP has its own `PACKAGE_MANIFEST.json`.

Implementation, testing and documentation were assisted by OpenAI Codex and
Anthropic Claude Code. The student's own decisions, testing experience and
contribution are described in the final report. The measured results and
limitations are retained without claims of unaided implementation or unmeasured
performance. An earlier lost-computer experiment was not recovered and is not
treated as reproduced evidence.

Primary research references and access limits are documented in
[Korean related work](docs/KOREAN_RELATED_WORK.md) and
[English related work](docs/ENGLISH_RELATED_WORK.md).

LolAi.gg is not endorsed by Riot Games. League of Legends and associated
properties belong to Riot Games.
