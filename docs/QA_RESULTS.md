# LolAi.gg observed verification results

Updated: 2026-10-30 (Asia/Seoul), with earlier checkpoint history retained below. These checks concern localhost/private research, not public deployment.

## Historical original deep-learning MVP

The user confirmed deep learning is mandatory and supplied the October 30 23:59 deadline. Earlier uploads/screenshots are samples, not final submission evidence. A fixed 6-16-8-4-1 ReLU/sigmoid MLP with 289 parameters is trained and installed. See DEEP_LEARNING_RESULTS.md for the negative exploratory evaluation and overfit gap.

At the original-MVP checkpoint, full-suite evidence was the user's normal Cursor terminal screenshot of check.cmd: `44 passed, 1 warning, 6 subtests passed in 40.93s`. The warning is a dependency StarletteDeprecationWarning concerning httpx/httpx2. This supersedes the earlier incomplete restricted-shell full-suite attempts. The prior 17-model-test/six-subtest runs, TypeScript/production build, offline genuine ten-match neural analysis and independent metric parity checks also passed. The latter matched evaluation metrics within 1e-12 and confirmed unchanged data SHA, identical baseline partitions/scaler, and all training matches finishing before evaluation begins.

The original-MVP start.cmd screenshot showed server process 20304, application startup complete and Uvicorn running on http://127.0.0.1:8000. Subsequent fresh browser inspection and parsed JSON export verified neural model HTTP responses, the model/evaluation display, ten genuine-match neural estimates and export/report equality. Details and screenshots are recorded under the current verification section below. The older process's schema rejection and the earlier 39-test user-terminal result are historical checkpoints.

## Earlier logistic checkpoint

## Passed in the running browser

- Loaded the built React application and its labeled synthetic sample mode.
- Selected Live Riot API with Korea and the Riot ID entered by the user, Molybdite#KR1. The UI displayed Connected to Riot API, the matching player identity, and ten genuine completed ranked games.
- The observed ten-game summary showed 5 wins/5 losses, 50% win rate, 2.52 overall KDA, approximately 6.2 CS/min and 53% kill participation. These are this sample's descriptive statistics, not long-term skill estimates.
- Selected a different genuine match and verified the detail panel changed champion, KDA, duration and review prompts.
- Filtered Victories and observed only winning rows with a matching selected detail. Restored All results afterward.
- Before genuine-model installation, Model & evaluation correctly labeled synthetic training and real matches had no synthetic-model probability. After installation, genuine estimates displayed (for example 41% for the selected Karthus match), with the separate observed outcome.
- The rebuilt evaluation screen displayed Data source=riot, 83 training/21 test, accuracy 57%, majority baseline 48%, ROC-AUC 0.609, model Brier 0.264 and baseline Brier 0.260. The screen explains lower Brier is better. The match view explains the 9-10 minute snapshot and possible training overlap.
- Entered an incomplete Riot ID. The UI displayed the format error without losing the previous real result; restored the valid ID afterward.
- Pressed Tab from the Riot ID field and observed focus on Region.
- At the normal 648 px browser width, document width was also 648 px, with no horizontal page overflow. Other device sizes and complete accessibility testing were not performed.

## Data checks

Authenticated account, ranked match-list, match-detail and timeline requests completed through the running backend. The genuine responses are cached in SQLite. Local extraction validates match/timeline IDs, ranked/map eligibility, participant coverage, early snapshot features, finite values and winner labels. Raw cached records are appended with source=riot to the ignored backend/data/riot_matches.jsonl file, deduplicated by match ID.

Displayed kills/deaths/assists, outcome, champion, champion damage and CS/min were compared with the corresponding raw responses for each completed cached analysis. The permitted last-complete-frame window is minutes 9 to 10; observed snapshots are near minute 9 because the following frame's timestamp is slightly after the strict minute-10 cutoff. Do not claim exact 600-second observations.

Collection begins with the user-entered player and uses a small number of participants found in those ranked matches. This is a connected convenience sample, with player overlap and selection bias; it is not representative of the whole ranked population. No private/custom queues or undocumented data sources are used.

## Genuine model and automated checks

The exported snapshot contains 104 unique genuine records from six seed accounts; see REAL_MODEL_RESULTS.md for exact source, queue/patch/date coverage, classes, SHA and limitations. The trainer used 83 earlier/21 later matches. Independent recomputation of the saved JSON model on the held-out raw records reproduced accuracy 12/21, AUC 0.60909 and Brier 0.263561. IDs do not overlap across train/test, chronology is correct and preprocessing fits training only. Baseline Brier 0.259862 is better; no claim of improved probability quality is made.

The latest production frontend build passed TypeScript and Vite after adding baseline Brier and overlap/snapshot disclosures. All 11 prior ML tests passed again in 1.95 seconds; after adding the cache-version regression test, all 12 passed in 1.80 seconds. The initial rerun failed because Python TemporaryDirectory used a sandbox system temp folder with denied permissions; setting TEMP and TMP to an existing project .tmp/test-runtime directory resolved those failures. The complete asynchronous suite previously hit its bounded 35-second timeout in this restricted shell, so it is not recorded as a pass.

## Model-cache fix

Independent review found that saved analyses did not identify the installed model. The new backend keys analyses by SHA-256 of model artifact content, covering parameters and evaluation. Both fresh and stale lookups are isolated by version; a model change during awaited Riot calls prevents storing under the earlier version. Raw Riot responses and TTLs remain reusable. A focused regression test checks content changes; all 12 ML tests passed, and Python compilation passed. The genuine artifacts/data hashes were unchanged.

The user restarted successfully with start.cmd (server process 50780) after PowerShell blocked start.ps1. The restarted page displayed the new generic source-mismatch notice in sample mode. A real Molybdite#KR1 request then completed and saved a ten-match analysis under the current model-content hash at 2026-10-28 06:26:45 UTC. The saved response has source=live, model source=riot, the correct 83/21 evaluation, and ten probabilities within [0,1]. This verifies that the cache-version change is active in the restarted HTTP server.

## Earlier logistic checkpoint exports and remaining checks

At the earlier logistic checkpoint, JSON export was verified in Chrome for both fictional and genuine data. The in-app browser download interface could not confirm downloads, so the same button was exercised in standard Chrome. The saved Downloads/lolai-demo-analysis.json parsed correctly, retained DemoPlayer/source=demo, contained ten matches, and suppressed mismatched genuine-model probabilities. Downloads/lolai-live-analysis.json parsed correctly, matched Molybdite#KR1/source=live and ten genuine matches, included ten bounded genuine-model probabilities and the 83/21 report, and exactly equaled the corresponding saved API response. Neither file contained a Riot key-shaped value. No export code change was needed. These earlier exports do not verify the current neural version.

A clean-machine installation, full keyboard/accessibility checks, all screen sizes/regions and live upstream error cases remain unverified. At that earlier checkpoint the user's normal Cursor terminal passed 25 API cases, 2 collector cases and 12 ML cases, 39 total. The next expanded-suite checkpoint was the 44-test user-supplied pass recorded above; the later 135-test version 0.2.0 pass is recorded below.

The agent's shell still cannot resolve Riot hosts. Collection uses the same running application's documented /api/analysis endpoint, whose normal backend connection to Riot has been observed to work. Requests retain the backend's cache, allowlisted routing, pacing and shared Retry-After cooldown.

## Local evidence

Evidence screenshots are saved at screenshots/live-riot-dashboard.jpg and screenshots/real-model-evaluation.jpg, and screenshots/restarted-live-chrome.jpg. It contains no API key. Credentials and raw player datasets remain outside tracked source via .gitignore.

Final source check: the 40 nonignored source/evidence files and built frontend text assets contained no Riot credential-shaped values. backend/.env and the raw/model artifacts are confirmed ignored. Dataset SHA, active genuine-model report equality and disjoint train/test IDs were rechecked successfully. No source commit or remote push was performed.

## Historical restricted-shell full-suite attempts

With a writable project TEMP/TMP, the full suite still stalled in the first TestClient startup. A faulthandler trace shows socket.accept -> socket._fallback_socketpair -> asyncio ProactorEventLoop initialization, before application lifespan/test assertions. The run was stopped after 25 seconds. Diagnostic output remains in ignored .tmp/final-checks/pytest-latest.log. This agent-shell attempt was blocked before application tests. The subsequent user-run check.cmd in the normal second Cursor terminal passed all 39 tests; it uses mocked upstream requests and does not stop the existing server.

Test discovery completed successfully: 39 tests collected. The normal-terminal check.cmd launcher has its missing-dependency guard and command/path/temp configuration checked; the subsequent full 39-test execution passed in the normal Cursor terminal (user-provided output).

Final neural inference-cache check: the cache key includes an explicit inference-v2 marker as well as model-content SHA. This bypasses invalid neural payloads that an older still-running backend may have cached before restart. The unchanged raw Riot cache is retained. All 17 model tests and six subtests passed after this change in 4.99s.

## 2026-10-29 current deep-learning verification

Earlier on this date, a bounded 40-second run of the expanded 44-test suite in the restricted agent shell stopped before the first API assertion, during TestClient startup: socket.accept -> _fallback_socketpair -> asyncio ProactorEventLoop self-pipe -> anyio blocking portal. That historical run was incomplete, not an application assertion failure. No test process remained afterward. Diagnostic logs are ignored in .tmp/check_full_current.stdout.log and .tmp/check_full_current.stderr.log. The later normal-terminal pass below supersedes its pending full-suite status.

The earlier synchronous model run passed 17 tests and six subtests in 6.94 seconds. The user subsequently supplied the current normal Cursor check.cmd result: `44 passed, 1 warning, 6 subtests passed in 40.93s`. Its single warning is StarletteDeprecationWarning about the httpx/httpx2 dependency interface; it did not prevent the suite from passing. This evidence is user-supplied terminal output, not a successful rerun in the restricted agent shell. The private clipboard screenshots were not copied into tracked source.

The user also supplied current start.cmd output showing server process 20304, application startup complete and Uvicorn on 127.0.0.1:8000. This confirms restart and supersedes the earlier restart-pending status. The earlier restricted-shell localhost health probe was denied socket access and remains historical diagnostic evidence only.

A fresh in-app browser reload replaced the old invalid-artifact message with the expected demo/genuine-model source-mismatch notice. Model & evaluation displayed Trained Deep MLP, hidden layers 16-8-4, 289 parameters, source=riot and the 83/21 partition. Its rounded diagnostics showed 95% training accuracy, 48% evaluation accuracy and ROC-AUC 0.491, consistent with the stored 95.18%/47.62%/0.49091 values. Evidence: [restarted neural evaluation](screenshots/restarted-neural-evaluation.png).

Live Riot API lookup for Molybdite#KR1 returned ten genuine matches: 6 wins/4 losses, 60% observed win rate, 2.88 overall KDA, 6.3 CS/min, 43.55% kill participation and 1.21 vision score/min. Selecting Kayn match KR_8436869064 displayed a player-team MLP probability of 19.7069% (about 20%) alongside the observed win. Match patch 16.21.829.8620 and the resources hub's automatic 16.21 context were also checked. These are descriptive values for the displayed sample and a functioning inference example, not new held-out performance or causal advice evidence. Evidence: [restarted neural live analysis](screenshots/restarted-neural-live.png) and [selected Kayn match](screenshots/restarted-neural-match.png).

The actual Export analysis button saved Downloads/lolai-live-analysis (1).json, 45,071 bytes. Parsing confirmed source=live, the expected player identity, ten unique matches, method=mlp and trained_on=riot. All ten probabilities were finite and within [0,1]; summary wins matched the actual match outcomes. Exported model.evaluation exactly equaled the installed backend/data/model.json artifact's report field, including the [16,8,4] hidden layers and 289 parameters. No Riot-key-shaped value was present. This completes current neural HTTP/browser/export verification without changing application code, model parameters or evaluation numbers. The 104-match/83-21 exploratory evaluation and its quality limitations remain unchanged.

The final report review copy was rendered through installed Microsoft Word PDF export, because the packaged LibreOffice renderer is unavailable. All 40 pages were visually checked at 1191x1684 pixels, with fixes for cover clipping, chart labels, bibliography breaks and wrapped code. This is an editable Word reconstruction of the supplied HWP form. Native HWP conversion, school-format acceptance, adviser approval and personal reflection remain incomplete. Report files containing student identity are kept outside this source repository.

## 2026-10-29 learning resources and presentation

Added a resource panel for the selected champion/role with five official provider links and two encoded YouTube searches. The optional patch field is validated, resets when the selected match changes, and can use the match patch or publicly retrieved Data Dragon version. The two versions are labeled separately. No player ID/key is included in those external links. This is a link hub, not an integration of providers' internal data or a verified video recommendation system.

Three Node native helper tests passed, including malformed patches, query encoding and a real Data Dragon legacy-version-list regression. TypeScript and Vite production build passed. In the running browser, Data Dragon returned 16.21.1; selecting Orianna updated champion/role/search context; the 16.21 query encoded Orianna Mid patch 16.21 guide; malformed 16.21&bad=1 displayed an alert and removed guide links. The panel contained five provider links plus two YouTube links. At the observed 1280px viewport, document width was 1265px, with no page horizontal overflow. Evidence: screenshots/learning-resources.png. External destination content, video views/quality and other viewport sizes were not tested. This frontend check occurred before the later user-confirmed restart and does not verify neural MLP inference.

The user confirmed a free-format presentation is acceptable. The private 12-slide PPTX contains two editable charts, four editable tables and speaker notes on all slides. All previews were visually checked, package/geometry/font/native-value checks passed, and native PowerPoint opened the actual file without a repair warning. The native cover and results slide were inspected. No report, PPT or school portal submission was performed.

## 2026-10-30 review package

Report/PPT review copies now include the current 44-test/six-subtest pass and restarted neural runtime/export evidence. The report also describes the resource hub's limited scope. It remains40 pages; two changed pages were rendered and visually checked, and38 page images match the prior reviewed render byte-for-byte. The presentation changes only slide10 and its notes; that slide was rendered and inspected, and all other session slide objects match the prior version. New PPT package, geometry, font, native table/chart and first-party import checks passed; the documented Windows hard-link publication fallback copied identical validated bytes to a new output path.

A private73-file review ZIP contains current source, the prebuilt frontend, refreshed report/PPT and safe genuine MLP/logistic parameters with evaluation reports derived from those exact artifacts. Keys, raw match records, SQLite cache, dependencies and Git history are excluded. ZIP CRC, payload hashes and credential-shaped-value checks passed. Importing the packaged source/model using existing dependencies reproduced all ten previously exported genuine neural probabilities within1e-12. A clean-machine installation and exact retraining from a self-contained raw snapshot were not verified; the raw snapshot is deliberately absent. No application code or model parameters changed in this packaging step, and the earlier44-test result is not presented as a new test rerun.

## 2026-10-30 — version 0.2.0 feature extension

The new profile, sensitivity, temporal-model, benchmark, Riot-context and video paths have their own current record: [QA_FEATURE_EXTENSION_2026-10-30.md](QA_FEATURE_EXTENSION_2026-10-30.md). It supersedes old scope statements only for the newly implemented extension. The earlier original-MVP full-suite/live-browser evidence above is preserved separately. The user subsequently supplied the complete version 0.2.0 normal-terminal result: **135 passed, 1 warning, 6 subtests passed in 12.78s**. The nonblocking StarletteDeprecationWarning concerns the httpx/httpx2 TestClient interface; no dependency change was made. This full pass supersedes the earlier pending routing/collector gate, while independent live-browser checks remain separate evidence.


## Current complete suite evidence 2026-10-30

Source: the user pasted the final output of `.\GradProject\check.cmd` from the normal Cursor PowerShell terminal, run from the workspace parent. The server remained open.

```text
135 passed, 1 warning, 6 subtests passed in 12.78s
```

The warning is `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` It did not fail the run, and dependencies were not changed for it. The earlier 108-case focused agent-shell run and original-MVP 44-case full pass are historical checkpoints, not additional independent suites to add to the 135. This confirms current mocked API/collector/model execution; live Riot/YouTube success and exported-probability parity are documented separately. Clean installation, complete device/accessibility/error/quota paths, OP.GG connectivity and predictive/coaching quality remain unverified or limited. The new 43-page report and 15-slide presentation were rendered, visually checked and included with the current version 0.2 review snapshot. Earlier copies remain preserved. School format acceptance, student reflection and adviser review remain pending.
