# LolAi.gg 0.2 — implemented feature extension

This extends the previously reviewed graduation MVP. It does not recover the lost original computer or reproduce its reported 1,000-game/XGBoost experiment. The earlier 40-page report and 12-slide presentation remain preserved. The new version 0.2 review package includes the current source/build/models, a 43-page Word report and 15-slide presentation. All pages/slides were rendered and visually checked, and presentation package/layout/font/native evidence checks passed. Personal reflection, metadata, adviser review, school format acceptance and actual submission remain user review gates.

## Implemented now

- Recent role and champion profiles: games, wins, win rate, KDA, CS/min, kill participation and vision/min. All five roles remain visible; unseen roles have no invented rate. Most-played-role ties and unknown roles are explicit.
- Main-role versus other-role comparisons use the loaded sample, not an inferred preferred role or autofill label. Per-match comparisons exclude that match and require at least three other same-role games, preferring the same champion when enough exist. They use final statistics for retrospective review and are never fed into the historical predictor.
- Control wards placed and the game's surrender flag are shown when supplied. These fields do not establish AFK, intent, manners or team cooperation.
- Actual early-snapshot timestamps and six input sensitivity comparisons. Each substitutes one input with its training mean and reruns the saved model. These changes are not SHAP, causal effects, additive contributions or recommended actions.
- Recorded champion kills, towers, inhibitors and major-monster events provide review timestamps.
- An actual probability timeline uses **11 separately trained MLPs for target windows ending at minutes 5–15**. The recorded frames are approximately minutes 4–14, and the graph uses their actual timestamps. Targets 16–20 were skipped for insufficient holdout samples. The original active model and its 47.62% result remain unchanged.
- A locked-split Random Forest benchmark is now measured and displayed with logistic regression. RF: **14/21 correct (66.67%), AUC 0.590909, Brier 0.260681**. Its Brier score is slightly worse than the constant prior (0.259862); it has not been selected to replace the MLP. XGBoost has a conditional benchmark path but is not installed or evaluated in this environment.
- On-demand current Riot rank and champion mastery use backend-only authentication and the platform's Riot host. Current account context is clearly separate from historical match-time information and model features. These calls have mocked checks and now a verified live browser response for Molybdite#KR1 after the 0.2.0 restart: current Bronze II/73 LP and Sylas mastery level 9/71,768 points. This does not verify all region/error/empty paths.
- YouTube Data API search and video detail retrieval are implemented behind a manual button. Sort by views or newest within 14/30/90 days; show channel, publication date, views and whether the entered patch appears in the returned text. Results require a separate backend `YOUTUBE_API_KEY`. After the key was configured locally and the server restarted, an actual Ahri/Mid/16.21/most-viewed/30-day query returned video metadata; the absence of a patch mention was correctly labelled. Search links still work without this key. A patch text match and high view count do not verify gameplay patch coverage, expertise or advice quality.
- A bounded, fixed-endpoint OP.GG MCP schema discovery script is implemented. The actual request failed with a connection/DNS error here. No successful discovery, tool call, build feed, leaderboard feed or full provider integration is claimed.

## Engine and experiment evidence

- **Earlier focused checkpoint: 108 backend checks plus six subtests passed** for the model, profiles, context, videos, benchmark, artifact handling and new endpoint-function/mocked-flow paths. The two flow checks exercise lifespan, gateway, analysis and cache together with in-process HTTP mocks. They do not replace routing/middleware or real upstream checks.
- **Current complete suite: 135 passed, one warning, six subtests passed in 12.78s.** This is user-provided `check.cmd` output from the normal Cursor terminal and includes the current TestClient/collector cases. The StarletteDeprecationWarning did not fail the run; no dependency change was made. The earlier restricted-environment socket stall and original-MVP 44-test pass remain historical checkpoints.
- **13 frontend checks**, TypeScript and the Vite production build passed after the final search-form update. The 10/20-match selector and old-backend restart notice were first exercised against the earlier running server. The new backend was subsequently restarted and its major successful browser paths verified separately.
- Using ten saved genuine Riot research records produced five role groups, nine champion groups, ten personal comparisons, 110 temporal estimates and 947 recorded events. All temporal estimates were finite in [0,1]. This is an integration smoke check on saved records, not fresh Riot retrieval or independent model evaluation.
- Independent NumPy calculations reproduced 227 held-out timepoint probabilities across the 11 models (maximum difference 1.72e-15) and all recorded accuracy/AUC/Brier metrics. Those 227 timepoints repeat the same 20–21 holdout games; they are not 227 independent games.
- Production components were rendered from this saved-record output and inspected in the browser, including profile groups, disclosures, probability curve, sensitivity and benchmark. No horizontal body overflow or browser console errors were observed at the checked desktop size. This earlier check was a static component preview. It was followed by a real version 0.2.0 browser/API check described below.
- After the user restarted the server, `/api/health` reported `ok` and version `0.2.0`. The real application displayed the demo profile and MLP/RF comparison, then retrieved ten genuine Molybdite#KR1 KR games (5W/5L). Selected Sylas match `KR_8437811854` displayed the actual 9:00 snapshot, six sensitivity rows and eleven temporal estimates. Current Riot rank/mastery loading succeeded; these current values remain separate from historical prediction inputs.
- A real YouTube response for Ahri/Mid/16.21, most-viewed order and the last 30 days returned one video: [How to Climb With AHRI Guide - S16 League of Legends](https://www.youtube.com/watch?v=BnwE5CD1-qA), Coach Mysterias, published 2026-10-02, observed 22,765 views. The UI correctly labelled the patch as not found in text. Retrieval success is not evidence of relevant gameplay patch coverage, expertise or good advice.
- The new live JSON export was 393,515 bytes and contained ten unique matches, five role groups and six sensitivity rows per match. All ten main predictions and 110 temporal probabilities reproduced using the installed artifacts and existing cached raw responses; original evaluation metadata remained unchanged. No Riot/Google key patterns were found. The separate full 135-test run has now passed, but neither software checks nor this export independently validate predictive quality. Current rank/mastery and video panels are separate requests; their complete contents are not claimed as part of this export.

The original MLP remains weak, and most temporal models also compare poorly with simple baselines. The holdout was already viewed; all new comparisons are exploratory, with no new independent validation, calibration study or proof of user improvement. See [temporal experiment](TEMPORAL_MODELS.md).

## Run the existing prepared checkout

Restart the server in its Cursor terminal with Ctrl+C, then run this from any PowerShell folder:

```powershell
& 'C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트\GradProject\start.cmd'
```

Open http://127.0.0.1:8000/ and refresh. `/api/health` should report version `0.2.0`. Analyze a real Riot ID, choose the requested sample size, inspect the role/champion sample, and expand the selected match's probability timeline/input review. Current rank/mastery and video results load only when their buttons are pressed.

Run checks separately without stopping the server:

```powershell
& 'C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트\GradProject\check.cmd'
```

Optional video configuration: put `YOUTUBE_API_KEY=your_key` only in `backend/.env` and restart. The Riot key cannot authenticate YouTube. Do not put either key in chat, the frontend or Git. API authentication and current video fields follow [Google's key guidance](https://docs.cloud.google.com/docs/authentication/api-keys-use), [search.list](https://developers.google.com/youtube/data/reference/rest/v3/search/list) and [videos.list](https://developers.google.com/youtube/data/reference/rest/v3/videos/list).

## Research commands

From GradProject, using the prepared environment:

```powershell
.\.venv\Scripts\python.exe backend/scripts/train_timeline_models.py --input backend/data/riot_matches.jsonl --reference backend/data/model.json
.\.venv\Scripts\python.exe backend/scripts/benchmark_models.py --input backend/data/riot_matches.jsonl --reference backend/data/model.json
.\.venv\Scripts\python.exe backend/scripts/probe_opgg.py
```

The first two commands need the local ignored raw dataset and preserve the active model. Exact retraining is not self-contained in a distribution that excludes raw player records. The probe performs only schema discovery at [OP.GG's official endpoint](https://github.com/opgginc/opgg-mcp); it does not call an arbitrary tool or install a connection.

## Still unfinished

Actual OP.GG/FOW/GGQ/DEEPLOL/YOUR.GG data aggregation; a tested item/strategy recommendation engine; verified expert/video selection; behavior, communication or peer-feedback collection and consent; low-elo-specific training and ablation; real-time coaching/overlay; new independent evaluation and user studies; public hosting/authentication; and recovery of the original dataset/model. No school submission, adviser signature, Git push or public deployment has been performed.
