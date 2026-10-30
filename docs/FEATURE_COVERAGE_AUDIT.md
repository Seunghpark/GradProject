# LolAi.gg — requested features and the current rebuild

## Current verified source/runtime 0.6.0

The [0.6.0 completion record](COMPLETION_2026-10-30.md) supersedes overlapping
historical labels below. Purchase/undo/skill orders, native ordered-history
aggregates, ten-player minimum tip references, persistent private practice
tracking and website previous/next history controls are implemented. Full checks:
276 backend tests + six subtests, one warning; frontend 41 tests/build pass.
The separate store has 185 genuine games; original research 104 is unchanged.
The additional 35-game audit is retrospective and reports MLP 57.14%, AUC .67,
Brier .319481 versus logistic 80%, .873333, .168850. No neural-model improvement,
independent external validation or coaching benefit was established. Private
backups exist locally, with off-computer copying still required. New academic
copies passed native report/slides layout review and require final student/adviser
review, accepted school file-format confirmation and school submission.

Earlier increment:

## Current verified source/runtime: backend 0.5.0

The [collection update](COLLECTION_2026-10-30.md) implements automatic genuine-match
ingestion into a separate SQLite collection, native catalog/tip-reference refresh,
history pagination and a standalone match-detail API. Duplicate IDs do not inflate
the collection; partial timelines can upgrade saved records. The original JSONL
and trained artifacts remain unchanged. Initial import contains 104 matches.
Full normal-terminal checks: **252 tests + six subtests passed**, one nonblocking
warning, 28.05s. Live 0.5.0 pages grew the separate collection to **108 matches**,
with cache deduplication, refreshed 283-group catalog and saved detail reuse verified.
Demo records did not enter the collection. Website pagination/detail controls are deferred.

Previous verified 0.4.1 status:

The [0.4.1 implementation and live-check record](RANK_HISTORY_2026-10-30.md) and [full-suite receipt](QA_FULL_BACKEND_0_4_1_2026-10-30.txt) supersede conflicting older statuses below. **208 backend tests + six subtests** passed in the normal Cursor terminal (one nonblocking dependency warning); **40 frontend tests**, TypeScript and build passed. Current native features include ten-player scoreboards, role-opponent snapshots, recorded objective credits and death review windows, local champion/build/matchup aggregates, explainable tip priorities, practice targets, current Riot ranks with dated observations and optional OP.GG season archives. The archive is currently a backend API capability, with its dedicated website display deferred.

The frozen research dataset remains **104 genuine matches**. In 0.5.0 successful live
lookups feed a separate deduplicated collection and automatically refresh its own
catalog/reference snapshots. The API returns up to 20 games per paged request;
the collector supports 100 IDs per page with explicit start/pages arguments.
Item outputs still describe final inventories; ordered purchase/undo timelines
and skill-order aggregates are not implemented.

The active deep MLP still has **47.62% accuracy on the 21-game exploratory holdout**, with substantial overfitting. Functional test passes do not establish predictive or coaching quality. Independent evaluation, broader representative samples, learned player-metric impact weights, reliable tier cohorts, authenticated peer evidence and recommendation efficacy remain incomplete. The lost original XGBoost experiment has not been recovered.

Current user priority: program/backend reliability. Visual redesign and statistical skill-tier estimates are deferred; voice coaching and large real-time features remain outside this MVP. Source backups exist locally; an off-computer repository/data backup and clean-machine reproduction have not been verified. Existing report/PPT review copies predate these backend changes and are not final submission evidence.

## Historical inventory through earlier increments

The numbered sections below preserve earlier findings. Their older test counts and NOT BUILT/PARTIAL labels are historical when they conflict with the current status above.


Latest increment: [version 0.3.0 research tools](RESEARCH_TOOLS_2026-10-30.md)
adds verified actual OP.GG build-data calls, private unverified feedback, prospective
low-elo scripts and an opt-in own-stat client. It supersedes overlapping 0.2
implementation labels below. FOW/GGQ/DEEPLOL data integration, recommendation
efficacy, actual prospective evaluation and real-game checks are still incomplete.

Updated: 2026-10-30, Asia/Seoul. Scope: the current checkout and saved experiments. This audit distinguishes implemented code, observed checks and unavailable external evidence. It does not establish what ran on the lost computer.

**The full product vision is not complete.** The rebuilt historical-analysis MVP now also contains recent role/champion profiles, personal comparisons, current Riot rank/mastery lookup, input sensitivity, event markers, separately trained historical probability models, an RF benchmark and an on-demand YouTube API path. The user restarted version 0.2.0, and its demo/live profiles, model comparison, current Riot context, temporal/sensitivity panels, live JSON export and one actual YouTube metadata lookup were verified. The user-provided normal Cursor-terminal full-suite result is now **135 passed, one warning, six subtests passed in 12.78s**. Earlier original-MVP evidence remains separately recorded.

Labels: **DONE** means the named limited implementation exists; **PARTIAL** means a broader request remains incomplete; **RESEARCHED/ATTEMPTED** does not imply a successful provider integration; **NOT BUILT** does not mean impossible; **PRIOR RESULT** means supplied history that has not been recovered/reproduced.

## 1. Prior work and recovery

- **DONE — read the supplied proposal/materials and inspect GitHub first.** The linked repository was empty; original documents were preserved. See [source context](SOURCE_CONTEXT.md).
- **DONE — preserve the user's account of the previous prototype.** The user reported building it, iterating after poor advice/losses, and losing the computer. See [project history](PROJECT_HISTORY_AND_IDEAS.md).
- **PARTIAL — prior conversation consolidation.** Supplied notes were used; every old ChatGPT/Claude conversation, the lost PC, source and data were not independently recovered.
- **PRIOR RESULT — 10 players × 100 matches, about 10,000 player-match rows; LR 71%/AUC .77, RF 76%/.83, XGBoost 79%/.86.** These figures remain historical notes. The new 104-game experiments do not reproduce them.
- **NOT DONE — reconcile conflicting résumé periods or rewrite the Nexon/Kia/CJ/NH essays.** Their contexts are preserved without inventing a development period.

## 2. Platform and collection

- **DONE — React/TypeScript, FastAPI and SQLite.** Ranked historical lookup uses ACCOUNT-V1 and MATCH-V5; secure backend-only Riot headers, allowlisted regions, TTL caches, pacing, 429 handling, source labels and partial/fallback responses are implemented.
- **DONE — local launchers and fictional fallback.** `start.cmd` runs the prepared checkout; DemoPlayer#SKKU is explicitly fictional. The earlier MLP MVP was observed in the browser with genuine Molybdite#KR1 matches and a valid neural JSON export. A new version 0.2.0 live ten-match lookup and export have now also been verified after restart; the separate full 135-test run has also now passed in the user's normal Cursor terminal.
- **DONE — preprocessing and leakage controls.** Queue/map/participant/timestamp/numeric validation, duplicate-ID exclusion, train-only scaling and chronological partitions are implemented. This is a new Python/scikit-learn pipeline, not recovery of the former pandas source.
- **PARTIAL — collection scale.** The CLI appends/deduplicates recent matches for named accounts and preserves progress. The current genuine experiment has 104 unique KR games. Participant expansion, full-history paging and a production scheduled collector remain absent.
- **NOT BUILT — PostgreSQL/public operation.** No public hosting/domain, authentication, abuse protection or distributed production rate limiter. Local operation does not imply public-product approval.

Evidence: [main](../backend/app/main.py), [Riot client](../backend/app/riot.py), [cache](../backend/app/cache.py), [collector](../backend/scripts/collect_matches.py).

## 3. Models and measured results

- **DONE — active deep MLP.** 6→16→8→4→1, three ReLU hidden layers, sigmoid output, 289 parameters. Its saved weights remain unchanged. The 83 earlier training/21 later holdout experiment measures 10/21 correct (**47.62%**), AUC **.490909**, Brier **.372683**. Training accuracy is **95.18%**, consistent with substantial overfitting.
- **DONE — logistic regression and constant prior.** On the same split, LR is 12/21 (**57.14%**), AUC **.609091**, Brier **.263561**. Constant prior is 10/21 (**47.62%**), AUC **.5**, Brier **.259862**. Lower Brier is better.
- **DONE — new Random Forest benchmark.** A separate benchmark uses the unchanged split/features: 14/21 (**66.67%**), AUC **.590909**, Brier **.260681**. Its higher accuracy does not make it a demonstrated winner: its AUC is below LR and its Brier is worse than the constant prior. The active MLP is not replaced; no RF serving artifact is installed.
- **PARTIAL — XGBoost.** The benchmark includes a conditional XGBoost path, but XGBoost is not installed in this environment and no new XGBoost metrics were produced. Historical 79%/.86 remains unreproduced. No dependency was silently installed.
- **DONE — separate temporal MLP artifact.** Eleven models cover target minutes **5–15**, each trained separately using the same global train/holdout game assignment. Observed frames are approximately minutes **4–14**, not exact target timestamps. Targets **16–20** were skipped because too few eligible holdout games remained. No missing windows are interpolated/extrapolated.
- **NOT DONE — independent validation/calibration/improvement proof.** The holdout had already been viewed. RF settings and temporal experiments are exploratory extensions, not fresh validation or evidence of better coaching. Later temporal populations can differ. The 227 holdout timepoints reuse 20–21 games and are not 227 independent matches.

Evidence: [deep-learning results](DEEP_LEARNING_RESULTS.md), [temporal experiment](TEMPORAL_MODELS.md), [benchmark](../backend/scripts/benchmark_models.py), [comparison adapter](../backend/app/model_comparison.py), [model card](MODEL_CARD.md).

## 4. The nine remembered feature names

- **PARTIAL — gold_diff_10, xp_diff_10, cs_diff_10.** Team differences are inputs from the latest complete 9–10-minute frame; observed original training frames are near minute 9. Exact 600-second observations are not claimed.
- **PARTIAL — vision_score.** Displayed and used in descriptive review/personal comparison, not an early predictive input.
- **PARTIAL — control_wards_placed.** Optional post-match count from Riot `detectorWardsPlaced`; unavailable values stay null. It is not a model input or ward-quality score.
- **PARTIAL — role_winrate and champ_winrate.** Recent loaded-sample role/champion wins, counts and rates now exist. They are descriptive profile outputs, not pre-match personal-history features or predictive inputs.
- **NOT BUILT — objective_participation.** Observed team objective events are not individual objective-participation rates. Team tower/dragon input differences are a separate quantity.
- **NOT BUILT — worthless_deaths.** No operational labels or detector. Death totals cannot establish avoidability or intent.

The six prediction inputs remain team differences in gold, XP, CS, kills, towers and dragons. Full-match statistics and current rank/mastery are excluded from historical prediction inputs.

## 5. Dashboard and explanation

- **DONE — recent statistics, match selection/filtering, JSON export and gold timeline.** KDA, wins, CS/min, kill participation, vision and champion damage remain available.
- **DONE — actual early snapshot timestamp and six input sensitivities.** For each input, replace its blue-minus-red value with its training mean and rerun the same model; report the change in the selected player's team probability. This is model sensitivity, not SHAP, additive feature attribution, a causal effect or a recommendation. Correlated-input replacement can be unrealistic.
- **DONE — observed kill/objective timestamps.** Champion kills, towers, inhibitors and major monsters are shown with own/opponent/unknown team attribution when supplied. Events do not prove what decided the result.
- **PARTIAL — minute-by-minute probability timeline.** Separately trained supported windows now produce a historical curve, with actual frame times, gaps and per-window pilot metrics. It does not cover every minute, estimate an event's causal effect, or establish calibrated real-time probabilities.
- **DONE — descriptive post-match review and own-history comparison.** At least three other loaded same-champion/role or same-role matches are needed; the selected match is excluded. Later matches may be in the reference sample, so the comparison is explicitly post-match only.
- **NOT BUILT — item candidate scoring/build optimization or strategic choice engine.** No measured item/matchup/positioning/route advice benefit.
- **NOT BUILT — live client feed/overlay/voice coaching.** These were not implemented and tested to failure. No blanket claim that all real-time tools are prohibited or impossible is made.

Evidence: [analytics](../backend/app/analytics.py), [prediction review](../backend/app/prediction_review.py), [temporal serving](../backend/app/temporal_model.py), [frontend](../frontend/src/App.tsx).

## 6. Player profiles, lower elo and behavior

- **DONE — five-role and champion sample profiles.** Counts, wins, win rate, KDA, CS/min, KP and vision/min; no-game rates stay null. Most-played-role ties and unknown roles are explicit.
- **DONE — descriptive main/other-role gap.** Most-played role is inferred only from the loaded sample and is not a preferred-role or autofill classifier. Small-sample gaps are not a reliable skill difference.
- **DONE — optional current rank/champion mastery lookup.** A manual button requests `/api/player-context`, using LEAGUE-V4 and CHAMPION-MASTERY-V4. Current values are separate from the historical match and model. Missing/failed/empty context remains distinct; no fake context is supplied for DemoPlayer. A real response for Molybdite#KR1 was browser-verified: current Bronze II/73 LP and Sylas mastery level 9/71,768 points. These are current account values, not match-time labels or proof of expertise.
- **PARTIAL — surrender context.** An optional recorded game-ended-in-surrender flag exists. It is not AFK, completion-rate or intentional-feeding detection.
- **PARTIAL — personalization/recent form.** Own-sample comparisons exist, but there is no individually trained coach, validated form score or long-term improvement analysis.
- **NOT BUILT — specialist identity verification, lane/teamfight/farm/aggression/defense scoring, AFK/completion profiles or troll/intent classifiers.** Raw statistics do not label intention/personality.
- **NOT BUILT — chat/communication/manners/cooperation models and peer ratings.** No consent, labels, feedback storage or correction workflow has been implemented.
- **NOT BUILT — validated lower-elo model/behavior ablation or user improvement study.** Current rank context does not retroactively label the training games by rank. No high-elo→low-elo performance sequence, formal alpha/beta study or survey is claimed.

Evidence: [profiles](../backend/app/profiles.py), [current Riot context](../backend/app/player_context.py), [profile UI](../frontend/src/PlayerProfile.tsx), [context UI](../frontend/src/PlayerContext.tsx).

## 7. External services and videos

- **DONE — official OP.GG/FOW/GGQ/DEEPLOL/YOUR.GG links.** They remain separate services; no player ID is sent in these links. No internal score, paid feature or complete provider dataset has been merged.
- **RESEARCHED/ATTEMPTED — official OP.GG MCP.** A read-only discovery probe was implemented and attempted against its fixed endpoint. This environment returned a DNS/ConnectError; no initialization/schema discovery or tool call succeeded. This is not an integrated OP.GG build/specialist adapter.
- **DONE — champion/role/patch YouTube searches and optional API implementation.** A manual button can request recent video titles, channel, publication date and view count, with newest/most-viewed order and 14/30/90-day windows. The backend-only key is now configured in the ignored local environment. An actual Ahri/Mid/16.21/most-viewed/30-day lookup returned one video with channel, date and views; its missing patch-text match was correctly labelled. The not-configured/unavailable states and ordinary search links remain usable.
- **PARTIAL — patch matching.** Video patch mention is a text match, not verified gameplay coverage. A popular/recent video is not proof of expertise or good advice. No verified specialist/channel mapping or content-quality ranking exists.
- **DONE — Data Dragon version lookup and manual patch selection.** Regional client match version and public Data Dragon version remain distinct. No current-region live-patch confirmation or automatic patch-aware model adaptation.
- **NOT BUILT — all providers' features in one application.** No provider-data merge, scraping/iframe clone, item recommendation service, imported AI-Score/PLAYREPORT/team-luck score or paid-feature clone.
- **NOT INTEGRATED — G-Assist, Overwolf, Blitz and oracle-devrel/leagueoflegends-optimizer.** These are historical references only.

See [external scope and official references](EXTERNAL_INTEGRATIONS.md), [probe](../backend/scripts/probe_opgg.py), [YouTube backend](../backend/app/videos.py), [video UI](../frontend/src/VideoResources.tsx).

## 8. Checks: what actually passed

- **Historical full MVP suite:** the user's ordinary Cursor terminal passed **44 tests + six subtests**, 40.93s, one dependency warning. Those were the earlier 25 API/2 collector/17 ML cases. Earlier restarted-MVP browser/live/export checks were observed.
- **Current full backend suite:** user-provided normal Cursor-terminal `check.cmd` output: **135 passed, one warning, six subtests passed in 12.78s**. The warning is the nonblocking Starlette httpx/httpx2 deprecation notice; dependencies were not changed. The earlier focused agent-shell 108-test/six-subtest run remains a separate checkpoint.
- **Current frontend:** **13 tests**, TypeScript and Vite production build passed. Tests include empty/tied profiles, actual timestamps, signed sensitivity, temporal gaps, invalid video metadata/URLs and comparison availability. These are helper/static-render checks, not full browser automation.
- **Current model checks:** independent JSON forward passes, source guards, frame cutoffs, chronology, preserved active weights, sensitivity orientation and temporal metric reproduction passed. All 227 holdout timepoints match an independent NumPy calculation to numerical tolerance.
- **Current live browser/export checks:** version 0.2.0 status, demo profile and MLP/RF comparison, genuine Molybdite#KR1 ten-match lookup (5W/5L), selected Sylas snapshot at 9:00, six input sensitivities, eleven temporal points, and current Riot rank/mastery succeeded. An actual YouTube lookup succeeded. The 393,515-byte live JSON contained ten unique matches/five roles; all 110 temporal probabilities reproduced from cached raw responses, evaluation metadata matched the unchanged model, and Riot/Google key-pattern scans found none.
- **Pending:** clean-machine installation, every region/upstream error/device/keyboard path, quota/failure paths and load/security penetration checks. The earlier sandbox asyncio/socket limitation is historical environment evidence; the full current suite passed in the user's normal terminal.
- **Not proved:** useful coaching or general predictive quality. Passing engine tests does not improve the measured 47.62% original neural pilot.

See [QA evidence](QA_RESULTS.md). Keep historical and current checks separate.

## 9. Submission, backup and handoffs

- **DONE — original-MVP review package:** the preserved October 30 package contains a 40-page editable Word reconstruction and 12-slide free-format PPTX, source/build and original evaluated artifacts. It excludes secrets and private raw data. Adviser 한환수 is reflected; scores/signatures remain unfilled.
- **DONE FOR REVIEW — artifacts for the newest extensions.** A new 43-page Word report and 15-slide presentation cover version 0.2 features, live verification, 135 tests plus six subtests, and measured model limits. All pages/slides were rendered and visually checked; presentation package/layout/font/native table/chart checks passed. The new review ZIP includes current source/build/models and verification notes. Earlier packages remain preserved. **PENDING — student reflection/metadata, adviser review, school acceptance of the DOCX reconstruction and actual submission.** Raw-data-free packages cannot retrain the exact private experiment, and clean-machine installation is unverified.
- **DONE — proposed Codex/Claude/Cursor roles.** A coordination plan is not proof that a separate external Claude agent performed work. Cursor terminal evidence belongs to the observed user runs.
- **NOT DONE — student reflection/metadata confirmation, accepted final-report format, adviser review/online signature, school upload/email or Git push.** No final academic approval or submission was performed.

## 10. Remaining work

The full 135-test/six-subtest result is recorded from the user's normal terminal (12.78s, one nonblocking warning). The newest backend restart and successful sample/live/profile/context/timeline/export, current Riot context and actual YouTube metadata paths are now verified. Remaining external error/quota/device paths are separate checks. Repeat the OP.GG probe where DNS/network permits before calling it an integration.

The broader backlog still includes provider integration, reliable item/strategy advice, behavior/communication data with appropriate consent, dedicated lower-elo validation, independent model evaluation and user studies. The original dataset/results require recovery or a clearly separate new experiment. No overall completion percentage is assigned to differently sized features, and no unattended future work is promised.
