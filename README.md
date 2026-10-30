# LolAi.gg

**Resume in Claude Code:** read [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md), use the
[starter prompt](CLAUDE_START_PROMPT.txt), and check the
[submission gates](docs/SUBMISSION_READINESS_2026-10-30.md). These consolidate the
current state; the older release paragraphs below are historical records.

Graduation review files: [report PDF](submission/final_v06_2026-10-30/LolAi_FinalReport_v06_Review.pdf),
[editable report](submission/final_v06_2026-10-30/LolAi_FinalReport_v06_Review.docx),
[18-slide presentation](submission/final_v06_2026-10-30/소프트웨어학과_박승현(2019310202).pptx),
and [complete review ZIP](submission/LolAi_Review_Package_v06_2026-10-30.zip).
See [publication scope and private-data exclusions](docs/GITHUB_BACKUP.md).

Current source/runtime: **0.6.0**. [Implemented features, exact checks, later-period
evaluation and remaining boundaries](docs/COMPLETION_2026-10-30.md).
Ordered purchases/undo and skill histories, native sequence aggregates, stronger
tip sample rules, persistent private practice tracking and website history paging
are implemented. **276 backend tests + six subtests**, one warning, and **41
frontend tests**, TypeScript and production build passed. Live 0.6.0 controls and
APIs were checked. The separate collection has 185 genuine games; the original
104-game research snapshot/model are preserved.

An additional fixed-model audit on 35 newly collected later games measured MLP
57.14% / AUC .67 / Brier .319481, logistic 80.00% / .873333 / .168850, and constant
42.86% / .5 / .267321. This retrospective sample does not establish independent
generalization, neural superiority or coaching benefit. No model was replaced.
`backup-private.cmd` creates a verified private data snapshot; move it off this
computer separately. Keys are excluded. The 46-page report's native Word PDF
and the 18-slide presentation passed visual review. Student/adviser review and
the accepted school file format still need confirmation; no school upload occurred.

Previous increment:

Current source: **backend 0.5.0**. [Automatic collection, paged history, API examples and checks](docs/COLLECTION_2026-10-30.md).
Genuine lookups now save deduplicated matches and refresh native champion/tip-reference
statistics in SQLite. The API supports history offsets and standalone match details.
The original research JSONL and trained models remain unchanged. **252 backend tests
and six subtests passed** in the normal Cursor terminal (one nonblocking warning).
Live 0.5.0 checks grew the separate store from 104 to 108 genuine matches, verified
cached-repeat deduplication, refreshed catalog statistics and standalone details,
and confirmed demo exclusion. [Full check receipt](docs/QA_FULL_BACKEND_0_5_0_2026-10-30.txt).
The interface's new paging/detail controls are deferred. Existing frontend: 40 tests,
TypeScript and production build pass.

Earlier release: **0.4.1**. [Rank-history implementation, live checks and limits](docs/RANK_HISTORY_2026-10-30.md).
The native Riot-data core includes player analysis, full scoreboards, role-opponent
comparisons, champion/build aggregates, form trends, practice targets and explainable
local tips. Official current ranks now have persistent dated observations. An optional
OP.GG API route supplies provider-labeled previous-season archives, with a saved fallback.

**Previous 0.4.1 full normal-terminal checks: 208 passed, one warning, six subtests passed (23.78s).**
[Receipt](docs/QA_FULL_BACKEND_0_4_1_2026-10-30.txt). Existing frontend: 40 tests,
TypeScript and production build pass. Live health, Riot rank recording/cache behavior,
native catalog, genuine-player scoreboards/tips and the optional archive API were checked.
The dataset and active MLP hashes are unchanged. Restart with `start.cmd` after backend changes.

Current priority is program/backend reliability. Visual redesign, estimated skill tiers,
learned player-metric impact weights and actual-game coaching remain deferred.
The [tip formula](docs/TIPS_ENGINE.md) uses clearly labeled local references and equal
weights; current ranks and provider archives are not retroactively assigned to old matches.
The original XGBoost experiment remains unrecovered. No coaching efficacy is established.

The existing interface starts in **English**; **한국어 / English** saves your language
choice. The new optional archive feature is an API capability; its website card is deferred.
No report/PPT review copy or official school submission was silently updated.

Earlier implementation notes remain available: [native 0.4.0](docs/NATIVE_PLATFORM_2026-10-30.md),
[0.3 research tools](docs/RESEARCH_TOOLS_2026-10-30.md),
[post-match resources](docs/POSTMATCH_UPDATE_2026-10-30.md).

A local SKKU graduation-project MVP for historical League of Legends analytics. React/TypeScript and FastAPI provide Riot match analysis, recent role/champion profiles, personal comparisons and optional current rank/mastery context. A three-hidden-layer MLP supplies historical estimates, with input sensitivity, observed event markers, separate time-specific models and exploratory model comparisons.

Updated October 30, 2026: version 0.2.0 extensions are implemented; see [run steps and exact new features](docs/FEATURE_EXTENSION_2026-10-30.md). After the user restarted the server, version 0.2.0 was verified through the real browser: profiles, current Riot rank/mastery, temporal estimates, sensitivity, model comparison, live JSON export and actual YouTube metadata all worked. The user supplied the normal Cursor-terminal result: **135 passed, one warning, six subtests passed in 12.78s**. The earlier 44-test pass remains historical evidence for the original MVP. The full provider-merge/coaching vision is not complete; see [exact coverage](docs/FEATURE_COVERAGE_AUDIT.md).

The linked GitHub repository was empty when inspected. Original proposal and report materials were read without modifying them. See docs/SOURCE_CONTEXT.md for the scope and evidence notes.

For Codex/Claude/Cursor assignments, acceptance gates and prompts, read [the team handoff](docs/TEAM_HANDOFF.md). For a short working presentation, use [the demo script](docs/DEMO_SCRIPT.md). Korean [report content](docs/REPORT_CONTENT_DRAFT.md) and [presentation content](docs/PRESENTATION_CONTENT.md) are source drafts. The new October 30 version 0.2 review package includes a 43-page Word report and 15-slide presentation with current features, live checks and measured model limits. All report pages and slides were rendered and visually checked; presentation file/layout/font/native-table/chart checks passed. The earlier 40-page/12-slide MVP package and 101-file extension snapshot remain preserved. The Word report is a reconstruction based on the official HWP form; school acceptance of DOCX is unconfirmed. No school submission has been performed.

## Run on this Windows computer

The dependencies and frontend build are prepared in this checkout. A genuine 104-match deep MLP (6-16-8-4-1) is installed locally; a fresh checkout still creates a labeled synthetic demonstration model. In PowerShell:

```powershell
cd 'C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트\GradProject'
.\start.cmd
```

The start.cmd launcher works from Cursor PowerShell without changing its script execution policy. Open http://127.0.0.1:8000 in your browser. Stop the server with Ctrl+C. Use `./start.ps1 -Port 8001` if the default port is occupied. The frontend and API are served by the same process. API documentation is at http://127.0.0.1:8000/docs. Restart an old running process after the new backend changes, then refresh the browser. An earlier open server does not automatically load these additions.

If PowerShell reports PSSecurityException or UnauthorizedAccess for start.ps1, use start.cmd above. The equivalent direct command from the project root is:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

For a fresh checkout, install Python 3.11+ and Node.js 20.19+ (or 22.12+), then run:

```powershell
.\setup.ps1
.\start.cmd
```

Setup installs Python and frontend dependencies, builds the frontend, and creates a clearly labeled synthetic model if no model already exists. It uses pnpm when available, the bundled Codex pnpm on this computer, or npm. Local package caches, virtual environments, runtime data, and credentials are ignored by Git.

## Demonstrate the current checkout

1. Keep Sample demo selected and analyze DemoPlayer#SKKU. The identity and matches are fictional; genuine-only model artifacts intentionally suppress fictional probabilities.
2. Choose 10 or 20 recent matches, then select Analyze player; changing the count alone does not fetch new data. Inspect the five-role/champion sample profile and most-played versus other-role comparison. Empty groups have no observed win rate; ties/unknown roles are explicit. These are loaded-sample statistics, not skill/mastery/autofill scores.
3. Select a match or filter results. Inspect statistics, optional control-ward/surrender context, gold timeline, actual early snapshot time, six input sensitivities and observed kill/objective timestamps. Personal comparisons need at least three other same-role games and exclude the selected match.
4. For genuine estimates use Molybdite#KR1 on Korea with Live Riot API. Expand the historical probability timeline: separate supported target models 5–15 use actual frames around minutes 4–14. Missing targets remain gaps; no event-causality or calibration claim.
5. Use **Load current Riot context** to request current rank and selected-champion mastery. This is separate current data, not the old match's rank or a prediction input. A real current-rank/mastery response was verified after restart; it remains separate from match-time history.
6. Open Model & evaluation. Explain the unchanged active MLP, original baselines, additional RF comparison, unavailable XGBoost, tiny reused holdout and weak probability quality.
7. Export analysis as JSON. Check that all extension fields and model references match the visible result after restarting the newest server.
8. In Learning resources, open official provider/search links. The manual video-results button supports recent/newest/most-viewed metadata through the optional YouTube API; without a backend key it explains the missing configuration rather than inventing videos. A backend key is now configured locally, and a real Ahri/Mid/16.21 search returned video metadata. The result correctly said that the patch was not found in the video text; this was not a quality endorsement.

The active original MLP uses 104 genuine KR games, 83 earlier train/21 later holdout, 16–8–4 hidden ReLU units and 289 parameters. Its exploratory accuracy is **47.62%**, AUC **.490909**, Brier **.372683**; LR **57.14%/.609091/.263561**; constant prior **47.62%/.5/.259862**. Training accuracy **95.18%** versus evaluation **47.62%** is consistent with overfitting.

The new RF benchmark on the unchanged split is **14/21 = 66.67%**, AUC **.590909**, Brier **.260681**. RF is not a demonstrated overall winner: LR has higher AUC and the constant prior lower Brier. The active MLP is unchanged. The benchmark has a conditional XGBoost path, but XGBoost is not installed and no new XGBoost metrics exist. The lost historical 1,000-game/XGBoost 79% experiment is not reproduced.

The temporal artifact contains 11 separately trained MLPs for targets 5–15; targets 16–20 lack enough eligible holdout games. Actual recorded frame times differ from target minutes. Later populations differ; 227 holdout timepoints repeat 20–21 games. These are exploratory reused-holdout results, not fresh validation, calibrated probabilities or proven user benefit. Read [original MLP results](docs/DEEP_LEARNING_RESULTS.md) and [temporal experiment details](docs/TEMPORAL_MODELS.md).

Deep learning is mandatory. Confirmed final deadline: **October 30, 2026, 23:59 KST**. The official report HWP is preserved; the earlier Word reconstruction/PPT were reviewed for the original MVP. Student reflection, final metadata/file-format acceptance, adviser review/online signature, consistency with the chosen source version and actual upload remain pending. See [submission requirements](docs/SUBMISSION_REQUIREMENTS.md).

## Enable real player lookup

Copy backend/.env.example to backend/.env and set RIOT_API_KEY there, or set the environment variable before starting the server. Restart the backend after changing it. Never put this key in frontend files or a VITE_ variable.

```powershell
if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
```

Edit backend/.env locally, choose the appropriate region, enter your actual GameName#TAG, select Live Riot API, and analyze. Do not use DemoPlayer#SKKU for a live lookup. Development keys expire; obtain a current key through https://developer.riotgames.com/.

Live lookup resolves Riot ID through account-v1, then retrieves ranked match IDs, completed match details, and timelines through match-v5. The backend uses an allowlist for regional routes and sends the key only in X-Riot-Token over HTTPS. Fresh requests are conservatively paced; ten uncached matches can take roughly 30 seconds or longer. The UI remains in its loading state while the request completes.

Live mode reports missing/invalid keys, missing players, rate limits, and upstream failures. Auto mode can use cached results or explicitly labeled sample data when Riot is unavailable; a missing player still returns an error. A synthetic fallback always shows the fictional sample identity. Partial results retain a warning. Analysis caches are versioned by model artifact content and inference implementation so a model replacement cannot reuse previous predictions. Fresh analysis is cached for five minutes; raw completed matches/timelines can be reused for seven days. Stale fallback is limited to seven days. There is no forced-refresh control in this MVP.

After restart, version 0.2.0 retrieved ten genuine Molybdite#KR1 KR matches (5W/5L). The browser displayed five role groups, personal comparisons, selected-match snapshot/sensitivity/temporal panels and current rank/mastery. The exported live JSON reproduced all ten main estimates and 110 temporal probabilities using the installed artifacts and cached raw responses. This is a successful path check, not broad provider or predictive-quality validation. Inference refuses mismatched data sources, so a synthetic model cannot predict genuine games and a genuine model cannot predict fictional fixtures. Individual match examples may overlap training data; use only the separate holdout to assess quality. See docs/QA_RESULTS.md for checks and limits.

## Optional video metadata and current Riot context

Current rank/mastery reuses the configured Riot key and is requested only by its manual button. `/api/player-context` resolves the ID, then uses LEAGUE-V4 and CHAMPION-MASTERY-V4 with a five-minute cache. Missing/empty/failed values remain distinct; DemoPlayer is fictional and does not request current account context. Current values are excluded from historical model inputs and cannot label old training games by tier.

`/api/videos` supports the selected champion/role/optional patch, newest or most-viewed order and a 14/30/90-day publication window. It returns up to six YouTube metadata results with a six-hour cache. For a new installation, set `YOUTUBE_API_KEY` only in the ignored backend environment and restart. This checkout is now configured and one actual video lookup succeeded. Without it, ordinary search links remain available and the API returns `not_configured`. Network/quota errors return `unavailable`; no fictional videos are returned. A patch-text match and high views do not verify coverage, expertise or advice quality.

Official OP.GG MCP discovery was attempted with `backend/scripts/probe_opgg.py`, but DNS/ConnectError prevented connection. No initialization/schema query or tool call succeeded, and no provider data/build/specialist integration is installed. See [external scope](docs/EXTERNAL_INTEGRATIONS.md).

## Collect and evaluate genuine matches

Use several real players with sufficient ranked history; repeated players can share matches, so the collector deduplicates match IDs and preserves progress when a Riot request fails. Local research only; do not commit raw player data.

```powershell
.venv/Scripts/python.exe backend/scripts/collect_matches.py --riot-id 'PlayerOne#TAG' --riot-id 'PlayerTwo#TAG' --platform kr --count 100
.venv/Scripts/python.exe backend/scripts/train_model.py --input backend/data/riot_matches.jsonl --output backend/data/riot_mlp_model.json --algorithm mlp
```

Set MODEL_PATH in backend/.env to the absolute path of riot_mlp_model.json and restart. Review riot_mlp_model_evaluation.json before reporting results. The minimum is 100 eligible unique matches; this is a technical training threshold, not enough evidence for broad accuracy claims. See docs/MODEL_CARD.md for filtering, features, chronology, leakage controls, and limitations.

Prediction features are blue-minus-red gold, XP, CS, kills, towers, and dragons through the latest complete frame between minutes 9 and 10. One row per match is split chronologically. The scaler fits training data only. Neural weights/biases and logistic parameters are saved as bounded plain JSON. Serving performs the forward pass without sklearn and never loads pickle. Final KDA/damage are used only for post-match feedback, and the winner is used only as a training label.

The optional `backend/scripts/train_timeline_models.py` produces the separate temporal artifact from the same private raw input and saved reference split. `backend/scripts/benchmark_models.py` runs the additional fixed-split LR/RF/conditional-XGBoost comparison. Both preserve the active MLP, distinguish exploratory reused-holdout evidence, and do not recover the lost experiment. Use their documented defaults/help and retain the generated provenance reports. Runtime inference needs saved artifacts, not raw JSONL; raw-data-free source packages cannot retrain the exact private experiment.

## Development and checks

From a second Cursor terminal at the project root, leaving the server terminal open:

```powershell
.\check.cmd
```

This uses the existing virtual environment and a writable project temporary folder. It does not need a Riot key or make genuine Riot API calls: upstream responses are mocked. The equivalent command is `.venv/Scripts/python.exe -m pytest -q --basetemp=.tmp/pytest-cli` after setting TEMP/TMP to an existing writable temporary directory.

The API tests mock Riot rather than spending real API quota. Model tests exercise leakage, incomplete frames, team orientation, source guards, deduplication, train-only preprocessing, and chronological evaluation. Collector tests mock the network and check append/deduplication behavior. This restricted Windows execution environment needs permission for local sockets to run asynchronous API/collector tests; otherwise asyncio initialization can stall before application code. If tempfile raises PermissionError, set TEMP and TMP to an existing writable project .tmp directory for that terminal session.

To edit the frontend with automatic reload, run the backend and then `pnpm dev` or `npm run dev` from frontend in a second terminal. Open http://127.0.0.1:5173. Build changes with `pnpm build` or `npm run build`; restart is unnecessary for static assets. If building in this restricted Windows environment, first create frontend/dist/assets with PowerShell. Old hashed assets are retained to avoid its directory-recreation restriction; remove dist before packaging a release in a normal terminal.

Verification is split by version:

- **Original MVP:** the user's normal Cursor terminal passed all 44 tests and six subtests in 40.93s, one dependency warning. A restarted browser showed the trained MLP, real ten-match lookup and valid JSON export matching the installed report. This is historical evidence for the earlier build.
- **Newest full backend:** the user's normal Cursor terminal passed **154 tests and six subtests in 26.75s**, with one nonblocking StarletteDeprecationWarning. This covers the current 0.3.0 suite, including routing/collector cases. The 135-test/six-subtest pass in 12.78s applies to the preceding 0.2 version. The restricted-session 127-test/six-subtest pass remains separate evidence.
- **Newest frontend:** 13 helper/static-render tests, TypeScript and Vite production build passed. These cover profiles, timestamps, sensitivity, temporal gaps, video metadata/state and benchmark availability. They are not full browser tests.
- **Numerical checks:** original and temporal JSON inference/metrics match independent calculations; the active artifact remains unchanged. The 227 temporal holdout points are repeated observations of the same small game set.

The full `check.cmd` result is now recorded from the user's normal Cursor terminal: 154 passed, one warning, six subtests passed in 26.75s. The preceding 0.2.0 browser evidence remains preserved; the new 0.3.0 browser checks include genuine Riot/item/cohort responses, actual OP.GG build data, synthetic live stats and bilingual responsive panels. Full clean-install, all regions/errors/devices, keyboard/accessibility, quota/failure paths and load/security checks remain unverified. See [QA evidence](docs/QA_RESULTS.md) and [the current research-tools checks](docs/RESEARCH_TOOLS_2026-10-30.md).

## Implemented scope and remaining work

Implemented: original historical Riot dashboard/cache/fallback/export/MLP pipeline; loaded-sample role/champion profiles and personal comparisons; optional ward/surrender context; manual current rank/mastery route; actual snapshot time, model sensitivity and observed events; 11 separate temporal MLPs; LR/RF/constant comparison and conditional unavailable XGBoost; manual optional YouTube metadata route; official provider/search links; tests and local launchers.

The version 0.2 review package now includes the latest verification notes, source/build/models and checked report/PPT revisions. Clean-machine installation remains unverified. Earlier snapshots are preserved. Confirm reflection, metadata, school file format and adviser review, then submit before the confirmed deadline; no upload or email has been performed.

Still not implemented: full OP.GG/FOW/GGQ/DEEPLOL/YOUR.GG integration, verified specialist/video-quality recommendations, reliable item/strategy engine, real-time overlay/voice, behavior/chat/peer-feedback data and consent/correction workflow, AFK/intent classifiers, validated multidimensional skill scores, dedicated lower-elo model/ablation, fresh independent evaluation/calibration/user-effect studies, public hosting/authentication. Current descriptive statistics and passing software checks do not prove these features or effective coaching.

The API remains a single-user localhost demonstration without public-use authentication or abuse protection. Original samples/historical claims are not adopted as new experiment results. No overall completion percentage is assigned to this mixed-size backlog.

LolAi.gg is not endorsed by Riot Games. Riot Games and associated properties are trademarks or registered trademarks of Riot Games, Inc. Technical and policy references: https://developer.riotgames.com/docs/lol and https://developer.riotgames.com/docs/portal.


