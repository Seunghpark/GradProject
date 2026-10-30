# LolAi.gg: start here to resume in Claude Code

Prepared October 30, 2026 (Asia/Seoul). This is the current handoff for the existing **0.6.0** program, not a new roadmap or a claim that every original idea was completed. Read the code before changing it. The immediate user request is to organize the work for Claude and assess submission readiness.

## 1. Open the existing project

- Local project: `C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트\GradProject`.
- Parent workspace: `C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트`.
- Public repository: https://github.com/Seunghpark/GradProject.
- The tested program snapshot was published at commit `6c9086556b80795dd75dc29d77162db4ec306431`. This handoff is a subsequent documentation update; inspect `git log -1` for the latest commit rather than resetting to that snapshot.
- Local `main` was synchronized with `origin/main`, with a clean working tree before this handoff update. Recheck it now. Do not reset or overwrite later user edits.
- Read [the decisions and conversation digest](docs/CONVERSATION_DECISIONS.md), [submission readiness](docs/SUBMISSION_READINESS_2026-10-30.md), and [the detailed 0.6.0 evidence](docs/COMPLETION_2026-10-30.md). Older README/handoff paragraphs are dated historical records and sometimes say that now-completed work is pending.

The owner originally had a local implementation on a lost computer. This is a working reconstruction on the office computer. Neither that lost source nor its claimed experiment has been recovered. Current source and evidence take precedence over recollections.

## 2. Immediate objective and constraints

The user wants a complete, demonstrable graduation project, originally within 3–4 days, with actual implementation rather than another multi-week plan. The supplied final deadline is **2026-10-30 23:59 KST**. Check the current clock: this date is not a reusable future deadline.

Deep learning is mandatory. The project is supervised by **한환수**. Student metadata in the review copies is **박승현 / 2019310202**; verify exact department/college and the registered title with the student. Free-format PPT was explicitly confirmed; a designated final-report HWP form was supplied.

Keep the direction: LolAi performs its **own analysis of Riot data**, with other providers as optional supporting references. It is not just a directory of links, and it does not reproduce proprietary providers' complete software. English is the default; Korean switching persists. Prioritize program/backend correctness before visual redesign. The user deferred actual-game testing, large real-time/voice coaching, and statistical skill-tier estimation. Ask before changing this scope. Make ordinary reversible fixes without repeated permission questions.

## 3. Run it on the current computer

In Cursor or Claude Code's PowerShell terminal:

```powershell
Set-Location -LiteralPath 'C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트\GradProject'
.\start.cmd
```

Open http://127.0.0.1:8000 and leave that terminal running. Use another terminal for commands. From the parent workspace, `.\GradProject\start.cmd` also works. To reload backend/configuration changes, stop the server with Ctrl+C, answer Y if Windows asks to end the batch, then run `start.cmd` again. Closing that server terminal stops the site.

Full backend checks, from the project directory:

```powershell
.\check.cmd
```

It selects the project's virtual environment, UTF-8, local temporary directory and pytest base path; it does not stop the server. Prefer `.cmd` launchers because this user's PowerShell policy blocked direct `.ps1` execution. Do not change the machine's global execution policy.

Frontend checks/build, using the already installed Node/package manager:

```powershell
Set-Location -LiteralPath 'C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트\GradProject\frontend'
node --test tests/resources.test.mjs tests/profile-review.test.mjs tests/i18n.test.mjs tests/research-tools.test.mjs tests/native.test.mjs
pnpm run build
```

`package.json` has no `test` script. It has `dev`, `build`, `preview`; a pnpm lockfile is present. If Node/pnpm is absent from PATH, inspect the configured runtime rather than installing arbitrary new dependencies. The previous session used the bundled runtime under `C:\Users\sh Park\.cache\codex-runtimes\codex-primary-runtime\dependencies`. A fresh-computer setup is described by `README.md` / `setup.ps1`, but was **not clean-machine tested**. Do not rerun setup unnecessarily on this working machine.

Riot and YouTube credentials already exist locally in ignored `backend/.env`; do not display them. Relevant variable names are `RIOT_API_KEY` and `YOUTUBE_API_KEY`. A clone of public GitHub does not include credentials, raw data, SQLite stores, dependencies or private backups. The model and aggregate report JSON files were deliberately published despite the broad data-directory ignore rules.

The prior restricted agent terminal could not reliably initialize sockets/DNS or connect to localhost; normal Cursor terminal and browser succeeded. Treat that as an environment distinction, not proof of a broken app. Do not copy old user terminal results as newly executed checks.

## 4. What is implemented

### Native player and match analysis

- React/TypeScript frontend, FastAPI backend, SQLite response caches and separate persistent match store.
- Riot ACCOUNT-V1 ID resolution; MATCH-V5 ranked histories, match details and timelines; current League rank/mastery context. Secure backend-only API headers, routing allowlist, paced requests, explicit rate/error/partial-data states, clearly labeled cached or sample-data fallback.
- History pagination and standalone match API; full ten-player scoreboards, team/player shares, lane-opponent early comparisons, final items/runes/spells, observed early deaths/objective credits and gold timeline. Statistics are page-specific, not a fabricated lifetime profile.
- Genuine lookups ingest deduplicated records and refresh native catalog/tip references. Demo records are excluded. The collection reached **185 genuine matches at the last verified snapshot**; later requests may grow it. It is not the frozen training dataset.
- Purchase/sale/consumption/undo and normal QWER skill histories. Known reversals are handled; ambiguous undo is shown and excluded from purchase-order aggregates. Missing/incomplete data is labeled, not invented.
- Native champion/role/patch/queue catalog, final inventories and first-six observed purchase/skill groups. These are descriptive frequencies, not validated optimal builds.
- Recent role/champion profiles and selected-match self-comparison using at least three other eligible observations; saved current-rank snapshots and previous-lookup changes.

### Original explainable review and practice

`backend/app/tips_engine.py` and `tips_config.json` implement the user's formula. For usable metric j:

```text
gap = max(0, (50 - performance_percentile) / 100)
weight = 1 / number_of_usable_metrics
consistency = recency-weighted fraction below the favorable median
priority = gap * weight * consistency
recency_weight = 0.85 ** older_game_index
```

Ties use midranks; lower early-death counts are favorable. Return up to three supported weaknesses plus one supported strength, without filling nonexistent findings. Display actual values, reference median, percentile, sample counts and factors.

Same-role/patch/ranked-queue references exclude the player and every loaded match. Per metric, require **30 distinct reference games, ten distinct reference players, and three recent observations**. Champion references require 50 games and a single reviewed champion. Missing values remain missing. Support CS/damage-share priorities are omitted. The fallback threshold dictionary is empty; no universal Gold threshold is claimed.

Metrics include CS/min, early CS, lane gold differences around 9–10 and 14–15 minutes, KP, damage share, vision/min, wards placed/cleared per minute, deaths before 14 and recorded major-monster participation. Exact snapshot times remain visible. Damage-taken share is descriptive rather than an assumed better-is-higher skill score.

Private practice supports CS/min, vision/min, KP percent and deaths. It freezes 3–10 earlier same-role/patch/queue games and compares only the first three later stored games. Save/reload/delete was verified; the disposable test target was removed. Private feedback is a local manual notebook, **not authenticated peer testimony**. Local-origin/marker checks are not Riot Sign-On or proof of player ownership.

### Models and supporting providers

- Actual three-hidden-layer MLP, JSON parameter validation/inference, logistic baseline, constant baseline and separate exploratory RF comparison. Eleven independent time-specific MLPs, actual input timestamps and noncausal sensitivity/event displays are implemented. This is not an LSTM or a proven causal explanation.
- Optional official OP.GG MCP discovery/workbench and a verified KR historical-rank archive backend endpoint. The archive has provider source/timestamps and saved fallback. A dedicated historical-archive website card remains deferred; do not claim all providers are merged.
- FOW/GGQ/DEEPLOL/YOUR.GG currently supply supporting links, not complete data integrations. No provider web scraping or proprietary-code import is part of this system.
- Actual YouTube metadata lookup with channel/date/views, sorting and 14/30/90-day windows. Patch text matching is labeled; it does not verify actual game patch, video quality or expert credentials.
- English default/Korean persistent switch, JSON analysis export, optional own-player Live Client stat-reader code and synthetic demonstration. Real in-game connection remains unverified/deferred; no live or voice coaching is claimed.

## 5. What remains incomplete or deliberately deferred

- **Not an all-features clone** of OP.GG, YOUR.GG, FOW, GGQ or DEEPLOL; full provider parity and public production hosting are unfinished.
- **No validated optimal item/strategy recommendation engine.** Existing inventories, observed sequences, review prompts, optional provider builds and retrospective item-choice coverage are narrower capabilities.
- **No learned player-metric impact weights/SHAP.** Tips use equal descriptive weights. The serving model has six team-difference inputs, so its weights cannot honestly become role-specific player-skill impact weights.
- **Tier data gap:** a guarded tier benchmark code path exists, but there is no usable tier cohort/UI. Batch participant current-rank enrichment, the requested explicitly estimated tier-at-fetch labels and lobby-average fallback are **not completed**. Existing prospective enrollment labels reject ranks fetched after the historical match; do not silently replace them with the proposed estimate mode.
- **Low-elo evaluation has zero eligible games/zero enrolled players** in the saved artifact. Enrollment/validation scripts exist; no low-elo superiority or improvement is established.
- No statistical rank-from-skill estimator, authenticated peer system, chat/communication/manners classifier, reliable AFK/autofill/intent inference or “worthless death” label.
- No causal coaching efficacy, user win-rate improvement, broad external validation or real-user alpha/beta study. Private practice tracking is not a controlled trial.
- No production authentication/abuse controls/load validation, verified clean installation, or completed actual-game acceptance. Do not bind this single-user app publicly as a deployment shortcut.
- Lost original experiment/source not recovered. Adviser acceptance, school format/title checks, personal review, school upload and private off-computer backup remain unverified.

See [submission readiness](docs/SUBMISSION_READINESS_2026-10-30.md) for the urgent academic gaps; do not attempt to implement every research/product ambition before today's deadline.

## 6. Exact results: keep the experiments separate

**Original frozen genuine KR dataset:** 104 unique matches; chronological split 83 training / 21 later holdout; one blue-side row per game. The holdout has already been inspected and is exploratory.

- MLP **6→16→8→4→1**, 289 parameters: training accuracy **95.18%**; original holdout accuracy **47.62%**, ROC-AUC **0.490909**, Brier **0.372683**.
- Logistic baseline on the original holdout: **57.14%**, **0.609091**, **0.263561**.
- Exploratory RF: **66.67%**, **0.590909**, **0.260681**; not the serving model.
- Constant training prior: **47.62%**, **0.5**, **0.259862**.

The six inputs are team differences in gold, XP, CS, kills, towers and dragons from the latest complete frame in the 540,000–600,000 ms window. Actual original frames are about **9 minutes**, not exact 10:00. Final-game statistics do not become historical prediction inputs. The 11 temporal models target minutes 5–15 with actual frames around 4–14; later windows lacked data. Repeated timepoints are not independent games.

**Separate later-period fixed-model audit:** model copies/hashes and 108 exclusions were saved before extra collection/performance calculation. At a 180-game collection snapshot, 37 older games were also excluded, leaving **35 later eligible games** (15 blue wins / 20 red wins). Seed-roster sampling was expanded from three to nine other players before calculating performance because only eight games were initially eligible. Results dated October 30, 18:12 KST:

- Unchanged MLP **20/35 = 57.14%**, AUC **0.67**, Brier **0.319481**.
- Unchanged logistic **28/35 = 80.00%**, AUC **0.873333**, Brier **0.168850**.
- Constant **15/35 = 42.86%**, AUC **0.5**, Brier **0.267321**.

This is a retrospective convenience-sample audit, not independent external validation. No model was retrained/replaced. The MLP still has worse Brier than the constant and logistic baselines. Comparing 21-game and 35-game accuracy does not prove an improved model.

Retrospective item-choice evaluation uses 83/21 original split, 210 holdout player rows, 95 covered: coverage **0.45238**, precision@3 **0.5940** versus global-frequency **0.1244**. It measures observed final-inventory agreement, **not item quality or increased chance of winning**; the holdout was already viewed.

The notes' old **1,000 matches / 10,000 player rows; LR 71%/.77, RF 76%/.83, XGBoost 79%/.86** are user-reported prior work from the lost computer, without recovered raw data/models/logs. Never present them as this reconstruction's measurements. A conditional XGBoost benchmark path is not a recovered trained XGBoost model.

## 7. Preserve these artifacts

Do not overwrite the raw JSONL, active models, frozen evaluation plan or earlier deliverables. In particular, `collect_matches.py` defaults to the original `riot_matches.jsonl`: inspect its CLI and use a **new explicit output path** for new studies. Normal app ingestion uses a separate SQLite store.

Frozen file SHA-256 values:

- `backend/data/riot_matches.jsonl`: `be988d94be1853b30b35ca6e3f8aaf4305be9a275a353666829e099bfe62368c` (104-game raw data; private).
- `backend/data/model.json`: `9a64650a4dade3b14c0370c999df8573b36da524cd6a413dee9b492a6cee017e` (active original MLP).
- `backend/data/riot_model.json`: `95e167e41f93f030c49a3ec89d0096da1f86fd7ca0cb074d5680e0981de973e1` (logistic model).

Other relevant files are `timeline_models.json`, `model_comparison.json`, `item_evidence.json`, `low_elo_evaluation.json`, `later_validation.json`; the private `later_validation_plan.json` records the frozen model copies/exclusions. Current raw collection is `match_store.sqlite3`; rank history and private feedback have separate databases.

Verified private backup: `.private-backups/20261030T095835552204Z`, 14 files, including the 185-game store, original JSONL, models and local research/private stores. Keys/caches are excluded. Consistent SQLite backup and file hashes were checked. **It is still on this computer.** Public GitHub does not preserve these private raw files; arrange an owner-controlled off-computer copy without publishing them. Do not upload credentials or unrelated office files.

## 8. Verification already recorded

- User's normal Cursor `check.cmd`: **276 passed, 1 warning, 6 subtests passed in 32.90s**. [Exact receipt](docs/QA_FULL_BACKEND_0_6_0_2026-10-30.txt).
- Restricted session separately: 246 passed, two deselected, six subtests; network/TestClient exclusions differ. Do not add these counts together.
- Frontend: **41 helper/static-render tests**, TypeScript and production build passed. They are not 41 full browser journeys or a production security assessment.
- Actual browser/API acceptance covered 0.6.0 health, genuine Molybdite#KR1 lookup, ten-player detail, purchase/skill history, honest tip samples, demo paging 0→10→0, Korean switch, fixed audit and persisted practice creation/reload/deletion. OP.GG archive and YouTube responses were verified in earlier increments.
- One Starlette/httpx deprecation warning remains; no dependency change was required to pass. There was no full clean-machine/public-production or real-game acceptance.

This handoff is documentation-only; the historical checks above were not rerun simply to generate new-looking receipts.

## 9. Code map and high-value reading order

- Routing/security/collection: `backend/app/main.py`, `config.py`, `riot.py`, `cache.py`, `match_store.py`.
- Native analysis: `analytics.py`, `native_review.py`, `loadout_timeline.py`, `native_catalog.py`, `profiles.py`.
- Own tips/practice: `tips_engine.py`, `tips_config.json`, `practice.py`, `feedback.py`.
- Model/measurement: `ml.py`, `temporal_model.py`, `prediction_review.py`, `model_comparison.py`; scripts `train_model.py`, `train_timeline_models.py`, `benchmark_models.py`, `evaluate_new_matches.py`, `build_item_evidence.py`.
- Tier/rank/providers: `player_context.py`, `rank_history.py`, `opgg_archive.py`, `providers.py`, `videos.py`, `live_client.py`; `enroll_low_elo.py` and `validate_low_elo.py`.
- Frontend orchestration/types: `frontend/src/App.tsx`, `types.ts`; native report/match/explorer, `ExplainableTips`, `SavedPractice`, `LaterValidation`, language helpers and `translations/`.
- Meaningful checks: `backend/tests/` and `frontend/tests/`; `check.cmd` runs pytest via root `pytest.ini`.
- Evidence/spec: `docs/COMPLETION_2026-10-30.md`, `TIPS_ENGINE.md`, `MODEL_CARD.md`, `RANK_HISTORY_2026-10-30.md`, `COLLECTION_2026-10-30.md`. Older cohort counts are dated snapshots, not current server totals.

## 10. Latest academic review files

Use **`submission/final_v06_2026-10-30/` inside this repository**:

- `LolAi_FinalReport_v06_Review.pdf`: **46 pages**.
- `LolAi_FinalReport_v06_Review.docx`: editable report reconstruction.
- `소프트웨어학과_박승현(2019310202).pptx`: **18 slides**, editable charts/tables/notes.
- `READ_ME_FIRST.md`: dated review-package instructions; its statement that Git had not yet been pushed describes the earlier packaging time. GitHub publication subsequently completed.

`submission/LolAi_Review_Package_v06_2026-10-30.zip` is a preserved dated 188-file review bundle; it predates these handoff documents. It excludes private raw data and is not the full private backup. Sibling folders in the parent workspace contain older drafts/source packages; do not treat them as the active checkout or silently replace the reviewed copies.

Report/source/PPT were visually reviewed. See `submission/QA/academic-artifacts.md`. Visual QA does not establish university acceptance. The supplied HWP remains unchanged at `C:\Users\sh Park\Downloads\연구논문작품_최종보고서.hwp`. The current PDF/DOCX is a reconstruction, not native HWP.

Read [the readiness checklist](docs/SUBMISSION_READINESS_2026-10-30.md) before announcing “finished.” Known concerns include related-work depth, inconsistent exact title strings across materials, unconfirmed accepted format and personal/adviser review. No signature, score, school upload, conference proof or email was performed.

## 11. Resume in this order

1. Read this handoff, check current date/time, Git status and actual artifacts. Summarize current implementation and urgent submission gates in plain language. Do not restart the app or rerun lengthy training by default.
2. Help the student resolve the exact title/format/personal/adviser checks. If time permits, improve the related-work section against the provided form using verified sources and meaningful comparisons; do not pad seven pages with repeated prose or invent source details. Some references were verified only through primary abstracts, as recorded in the related-work notes.
3. For academic edits, save a new revision and render/check it; preserve the existing reviewed PDFs/PPT and measured evidence. Keep narrative, metrics, figures, titles and slides consistent. Record what was actually checked. Student performs or explicitly authorizes school submission/contact.
4. For program work, first fix demonstrated defects in the current native core. Run appropriate backend/frontend tests for the change. Do not sacrifice the current runnable demo for broad feature parity before the deadline.
5. After submission priorities, agree the next bounded scope: e.g. optional archived-rank UI, separate clearly labeled estimated-tier enrichment, or prospective larger validation. Learned skill/impact/strategy features need a suitable new protocol and validation. Ask before adopting a new direction; do not start all of them simultaneously.

Claude Code can handle backend and documents as well as frontend; earlier AI role suggestions are coordination ideas, not a restriction. If multiple tools edit the repository, assign distinct files/tasks and review Git diffs before commits. Maintain one active checkout and one source of current evidence.

## Source coverage and limits of this digest

This handoff consolidates the visible conversation, the retrievable referenced “Vibe Coding Tool Comparison” chat, the supplied `LolAi.gg Project Notes.pdf` and the local code/receipts/artifacts. It is a practical state transfer, not a verbatim export of every ChatGPT/Claude conversation or a recovery of the missing computer. No credentials from the conversation are included. If an older recollection contradicts measured current evidence, retain it as reported history and investigate rather than silently upgrading it to a fact.
