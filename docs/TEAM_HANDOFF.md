# LolAi.gg team handoff and current completion gates

Current source/runtime: **0.6.0**. [Completion record](COMPLETION_2026-10-30.md)
supersedes older current-status claims below. Normal-terminal 276 tests + six
subtests passed (one warning, 32.90s); frontend 41 tests/build passed. Purchase,
skill, private practice and website paging features were checked. Separate store
185 games; frozen research 104; separate later audit 35. Neural accuracy 57.14%
and Brier .319481 do not establish superiority. Student/adviser/format/submission
and off-computer backup steps remain. The 46-page report PDF and 18-slide
presentation passed visual review; see submission/final_v06_2026-10-30.

Earlier records:

Current source: **0.5.0**. [Collection/pagination/detail implementation and checks](COLLECTION_2026-10-30.md).
Automatic genuine-match ingestion and transactional native-statistics refresh are implemented.
The API supports `start` offsets and standalone match details; website controls are deferred.
Full normal-terminal suite: **252 passed + six subtests**, one warning, 28.05s.
Restricted regression: 223 passed + six subtests. Live health reports 0.5.0;
two genuine pages grew the separate collection 104→106→108, with coherent catalog
revision 3. Cached repeats and standalone detail add no duplicate games; demo adds none.
The research JSONL, trained models and report/PPT review copies remain unchanged.
No retraining or new evaluation is claimed. See the linked record for limits.

Previous verified release:

Current source/runtime: **0.4.1**, with a user-confirmed full pass of **208 backend checks + six subtests**, one nonblocking warning, and 40 frontend checks. [Rank history and live endpoint verification](RANK_HISTORY_2026-10-30.md) supersedes older partial status below. Focus on program/backend code; visual redesign and statistical skill tiers are deferred. Current Riot rank observations and optional OP.GG archives are separate from historical model/benchmark labels. All source/raw/model/academic review artifacts are preserved.

Earlier notes:

Latest source/build: **0.4.0 native LolAi platform**. See [native coverage and validation status](NATIVE_PLATFORM_2026-10-30.md) and [the tested tip formula](TIPS_ENGINE.md). This supersedes the earlier UI-only status below. Current restricted-session pass is 153 backend tests + six subtests; 38 frontend tests and production build pass. The earlier 154-test full pass is historical 0.3.0 evidence. Preserve the dataset/model hashes and report/PPT review copies. External providers are optional; actual-game testing is deferred.

Earlier handoff notes:

Updated: 2026-10-30, Asia/Seoul. Continue the existing checkout; preserve its source, private data and artifacts. Codex/Claude/Cursor roles below are proposed assignments, not proof that an external Claude agent performed the work. See [detailed feature coverage](FEATURE_COVERAGE_AUDIT.md).

Latest UI update: English default with a persistent 한국어/English header switch.
All current application messages and known API notices are localized at display
time; research JSON and external proper names stay unchanged. Frontend now has
21 passing tests (previous 13 plus eight language tests), with TypeScript/Vite
passing and actual browser checks. See [language QA](QA_LANGUAGES_2026-10-30.md).
The earlier report/PPT/ZIP snapshots predate this UI update and remain preserved.

## Deadline and academic materials

Confirmed deadline: **October 30, 2026 at 23:59 KST**. Deep learning is required. Adviser: 한환수. The user confirmed free-format slides. Earlier uploaded samples are not completed final submissions.

The original October 30 MVP package (40-page report and 12-slide deck) and official HWP remain preserved. A separate version 0.2 review package now includes the current source/build/models, verification notes, a 43-page Word reconstruction and 15-slide PPTX. All report pages/slides were rendered and visually checked. Presentation package/layout/font/native table/chart checks passed; Windows denied the final hard link, so the validated bytes were published through an exclusive copy and matching hash. This is a review package. Native HWP/file-format acceptance, personal reflection/metadata, adviser review/online signature and actual upload remain pending. No signature, score, email, school submission or Git push was performed.

## Current implemented extension scope

- Existing React/TypeScript + FastAPI + SQLite MVP: Riot ID, completed ranked matches/timelines, source labels, secure backend key, caching, fallback, summary/detail, gold chart, rule-based review and JSON export.
- Recent five-role/champion counts and statistics, most-played versus other-role gap, null empty-group rates and explicit ties/unknown roles. Selected-match personal comparison uses at least three other loaded same-role or same-champion/role games; no individually trained coach or autofill classifier.
- Optional control-ward count and surrender flag; neither measures ward quality, AFK or intention.
- Manual current Riot rank/champion mastery request. Current context is not historical input or a retroactive training-game rank label. A real current-rank/mastery response was verified in the version 0.2.0 browser after restart; it is not historical match-time evidence.
- Actual early snapshot timestamp, six training-mean input substitutions and observed kill/objective markers. Sensitivity is noncausal and nonadditive; events do not prove why a game was won.
- Separate artifact with 11 time-specific MLPs for target minutes 5–15, actual frames about 4–14 minutes. Targets 16–20 skipped for insufficient holdout games. UI displays supported points at actual times, gaps and per-window metrics. See [temporal models](TEMPORAL_MODELS.md).
- New RF benchmark on the unchanged split and optional conditional XGBoost code path. RF is not installed as a replacement serving model; XGBoost is not installed and has no new result.
- Manual YouTube API panel with date/view ordering, publication window, metadata and cache/error states. The backend-only key is now configured locally, and one real Ahri/Mid/16.21/most-viewed/30-day result was retrieved with channel/date/views and an honest patch-not-found text label. Existing search/site links remain available.
- Read-only official OP.GG discovery probe attempted; DNS/ConnectError prevented connection. No successful MCP initialization, schema discovery, tool call or provider data integration.

## Measured experiments, kept separate

The active original MLP remains **6→16→8→4→1**, 289 parameters. Original data: 104 unique genuine KR games, 83 earlier training/21 later holdout. Original MLP: **47.62%**, AUC **.490909**, Brier **.372683**; training accuracy **95.18%**. LR: **57.14%**, **.609091**, **.263561**. Constant: **47.62%**, **.5**, **.259862**.

New RF benchmark: **14/21 = 66.67%**, AUC **.590909**, Brier **.260681**. Higher accuracy is not a demonstrated overall win: LR has higher AUC and the constant prior lower Brier. The active MLP is unchanged. Temporal results are separate per-window experiments; no best-minute selection or general accuracy claim. All use an already-viewed holdout; later eligible populations may differ. The lost historical 1,000-game/XGBoost 79%/.86 experiment remains unrecovered.

## Verification: historical versus newest build

- **Historical MVP full pass:** the user's normal Cursor terminal passed 44 tests and six subtests in 40.93s, one dependency warning. Those were 25 API, two collector and 17 ML cases. The restarted original MLP, real Molybdite#KR1 lookup and ten-match JSON export were observed.
- **Newest full backend pass:** user-provided normal Cursor-terminal `check.cmd` output for 0.3.0: **154 passed, one warning, six subtests passed in 26.75s**. The StarletteDeprecationWarning did not fail the run; dependencies were not changed. The prior 0.2.0 full pass (135 tests/six subtests in 12.78s) and focused restricted-session checks remain separate historical evidence. See [receipt](QA_FULL_BACKEND_2026-10-30.txt).
- **Newest frontend:** 13 helper/static-render tests, TypeScript and Vite passed. These cover profiles, timestamp/sensitivity, temporal gaps, video states/metadata and comparison availability; they are not combined browser/end-to-end checks.
- **Newest numerical checks:** independent forward/metric reproduction and preserved reference weights passed. Temporal checks reproduced 227 held-out timepoints across 11 models; those are repeated observations of 20–21 games, not 227 independent games.
- **Newest live success:** after restart, health reported 0.2.0. Demo profiles and MLP/RF comparison appeared; Molybdite#KR1 returned ten genuine games (5W/5L), selected Sylas snapshot 9:00, six sensitivities and eleven time-specific estimates. Current rank/mastery and an actual YouTube result succeeded. The 393,515-byte JSON export had ten unique matches/five roles; all 110 temporal points reproduced against cached raw responses, with unchanged evaluation and no Riot/Google key patterns.
- **Pending:** successful OP.GG network probe, clean installation, complete keyboard/narrow-screen, upstream/quota/failure and production/load/security checks.

Record new actual results in [QA_RESULTS.md](QA_RESULTS.md). Do not copy a historical pass into a new release without testing it.

## Immediate sequence

1. The user has restarted the current server and version 0.2.0 is verified. Keep that server terminal open; after any future environment/configuration change, restart `start.cmd` again.
2. The current complete `check.cmd` result is recorded: 154 passed, one warning, six subtests passed in 26.75s from the user's normal Cursor terminal. Preserve this evidence; rerun checks when later code changes justify it.
3. Preserve the now-observed demo/live profile, comparison, timestamp/sensitivity/temporal and export evidence. Extend coverage to untested keyboard/narrow-layout/error paths. A genuine-only artifact intentionally suppresses fictional probabilities.
4. Current Riot rank/mastery success and genuine Molybdite#KR1 source/export fields are verified; error/empty and other-region paths remain separate checks. Never print the key or put it in frontend settings.
5. Actual configured YouTube metadata retrieval is now verified, and the earlier not-configured state was also observed. Check quota/failure/empty cases separately without fabricating videos. Retry OP.GG discovery where DNS is available before implementing a verified tool adapter.
6. Freeze code after fixing demonstrated blockers. The separate 101-file source/model ZIP exists and predates current credential setup/live-verification notes. Create a new checkpoint if needed; preserve earlier packages and exclude keys, raw JSONL/SQLite, dependencies and unrelated private files. A raw-data-free package cannot independently retrain the exact experiment.
7. Decide which tested source version is submitted. Update report/slides to that version's verified scope, keep weak metrics and limitations, review reflection/metadata/file format with the student/adviser, rehearse and complete the required submission before the deadline. Existing original-MVP review copies remain preserved.

No unattended future completion is promised. Do not start a multi-week rewrite during final integration.

## Ownership for Codex, Claude and Cursor

**Codex — backend/model/final integration.** Own backend, scripts, tests, shared contracts and factual evidence. Coordinate every response field with the frontend. Check provenance, leakage, error handling and model/source compatibility. Never tune on the 21-game holdout to manufacture a better headline.

**Claude — assigned frontend polish or evidence-based writing.** Work only on explicitly handed-over files. Preserve the API, source labels and 0–1 rates; no rewrite or invented data. Report observed build/tests and return ownership before final integration. Report/PPT prose must distinguish implemented code from live verification and broader plans.

**Cursor — editor, ordinary terminal and QA/checkpoints.** Use the same checkout. First reproduce issues without concurrent edits. Record steps, expected/actual behavior and evidence; fix one assigned issue after ownership transfer. A user running Cursor is not evidence of a separate Cursor AI agent's implementation.

Shared rules:

- One active writer per file; transfer ownership before overlapping edits.
- Read README, [model card](MODEL_CARD.md), [temporal models](TEMPORAL_MODELS.md) and the current audit first.
- Keep Riot/YouTube keys in ignored backend configuration only. No raw player data or credentials in logs, bundles or source packages.
- Preserve old reports/artifacts; distinguish synthetic, genuine, cached and current-context data. No invented expert videos, behaviors, surveys or historical results.
- Run affected checks after changes. List changed files, exact observed results and unresolved checks before handoff.

## Prompts for the next explicit handoff

**Cursor QA:** Open the existing GradProject checkout and read README plus this handoff. Run the latest `start.cmd` and `check.cmd` in ordinary terminals. Inspect the sample and real KR analysis, profiles, current Riot context, temporal graph/disclosures, video not-configured/error/empty states, benchmark table and JSON export. Check keyboard and narrow layout. Record real defects with reproduction steps; do not rewrite owned files or expose keys. Do not mark unexecuted live integrations as passed.

**Claude UI/document pass:** Use only the files assigned by Codex. Preserve the current source/data contracts and exploratory model caveats. Improve clarity or prepare report/slides from verified current outputs, identifying which extensions were tested only by mocks/static render. Keep the existing original-MVP review package intact until a replacement has been reviewed. Return changed paths, checks and remaining issues.

## Still outside implemented scope

Latest frontend-only increment: [post-match learning update](POSTMATCH_UPDATE_2026-10-30.md).
Thirty frontend tests, TypeScript and build pass. Exact-patch localized item labels,
actual English/Korean OP.GG matchup guides and array-valued build display were
observed in the browser. Feedback deletion now asks for confirmation. The user
deferred the active-game test; polling is stopped and should not be re-enabled
unless the user resumes that test. Backend code/model/data were not changed.

October 30 update: [research-tools increment 0.3.0](RESEARCH_TOOLS_2026-10-30.md)
supersedes the list below where it overlaps. Actual OP.GG discovery/build calls,
private unverified self/peer notes, prospective cohort scripts and an opt-in own-stat
client are now implemented. The full provider merge, verified peer study,
recommendation efficacy, actual low-elo metrics and real-game validation remain open.

Complete OP.GG/FOW/GGQ/DEEPLOL/YOUR.GG feature/data merge; verified specialist/video-quality recommendations; reliable item/strategy engine; live overlay/voice; behavior/chat/peer-rating collection with consent and correction; AFK/intent classifiers; validated multidimensional skill scores; dedicated lower-elo training/ablation; fresh independent predictive/calibration/user-effect studies; public hosting/authentication. Current rank, descriptive stats and passing software tests do not satisfy these claims.
