# Master prompt: finish the existing LolAi.gg graduation project

Act as the lead engineer and academic-deliverable editor for my existing LolAi.gg project. Continue the actual checkout, verify the evidence, finish the bounded work needed for an honest graduation submission, and give me the finished files and exact submission steps. Do the work, not just a roadmap. I am not technical: keep progress updates short and explain any action I must take plainly.

## 1. Start in the right place

Work locally in this existing Windows folder:

```text
C:\Users\sh Park\Documents\ChatGPT\ㅈ조업 프로잭트\GradProject
```

Public repository: https://github.com/Seunghpark/GradProject

Read these before editing, in this order:

1. `CLAUDE_HANDOFF.md`
2. `docs/CONVERSATION_DECISIONS.md`
3. `docs/SUBMISSION_READINESS_2026-10-30.md`
4. `docs/COMPLETION_2026-10-30.md`
5. Relevant source, tests, model evidence and the supplied academic templates.

Check current date/time in **Asia/Seoul**, Git status, latest commit and existing outputs. The last synchronized handoff commit before this master-prompt update was `161f9af7bb45b22049819d71ad2bafd4228b2697`; this is a historical checkpoint, not an instruction to reset. Keep any subsequent edits. Older README/status paragraphs contain historical release notes; resolve conflicts against the actual source and dated evidence. Do not create another app, move to an old submission-source copy, or overwrite the working checkout.

The final deadline I supplied is **October 30, 2026 at 23:59 KST**. If it is still upcoming, prioritize a runnable, truthful submission over ambitious features. If it has passed, preserve the package and ask about the allowed submission route; do not invent an extension or claim a timely upload. Preparation can continue while an actual administrative fact is unresolved.

## 2. My project and decisions

This is an SKKU individual graduation project supervised by **한환수**. The review files use **박승현 / 2019310202**. Confirm exact department/college and registered title from available official materials or me before finalizing them.

The original proposal was “Deep Learning-Based League of Legend assistant.” I lost the computer containing an older implementation and am rebuilding on this office computer. My notes contain recollections and previous claimed results, not recovered experimental evidence. Earlier sample uploads/screenshots are not proof that final school submission is done.

**Deep learning is required.** We have a working React/TypeScript + FastAPI + SQLite application and an actual multilayer neural model. LolAi must perform its **own Riot-data analysis**, drawing inspiration from OP.GG, YOUR.GG, FOW, GGQ and DEEPLOL. Optional provider data/links support our program; they are not the core product or permission to copy proprietary code.

Keep English as the default with the existing persistent Korean switch. Focus functionality/backend reliability before visual redesign. I deferred actual-game testing, large live/voice coaching and estimated skill-rank modeling. Ask before changing this direction, replacing the architecture, adding a paid service, or introducing a large dependency. Ordinary necessary reversible fixes are authorized: do not stop to ask permission for each one.

## 3. Available tools: verify them, then choose the smallest useful set

Do not assume this pasted setup history proves that every plugin is usable in your current session or folder. Inspect your actual available tools, relevant installed skill instructions and project configuration. A configuration entry is not a successful connection. Report unavailable essentials once, use a practical fallback and continue independent work. Do not spend the submission window installing every optional tool.

Read-only inspection on this computer on October 30 found these **configured MCP server names** in the user's Claude configuration: `playwright`, `chrome-devtools`, `rea`, `firecrawl`, `perplexity`, `hyperframes`. It found `ponytail@ponytail` enabled in Claude settings. Their current runtime connectivity was not tested by Codex.

The pasted earlier Claude setup report additionally **claims**, but this handoff does not independently verify:

- Playwright, Chrome DevTools and REA connected.
- Ponytail, `/human`, `/humanizer`, Pro Design, Security Audit, Impeccable, Graphify, Agent Skills (25) and Replica (11) installed.
- Superpowers, GitHub and Engineering plugins still awaiting installation.
- Firecrawl and Perplexity awaiting usable API credentials; HyperFrames awaiting sign-in; graphify/skillspector possibly requiring a new session; `/human` voice samples not supplied.
- OmniRoute deliberately omitted; Watermarks Remover not installed. Other optional tools were deliberately skipped.

Use those only if actually available and relevant:

- **Ponytail:** smallest complete fix; preserve validation, security and accessibility. Reuse existing modules/dependencies, avoid broad refactors and unnecessary abstractions.
- **Playwright or Chrome DevTools:** use one available browser route for concrete local-app checks, screenshots and error reproduction. Do not run duplicate automation suites just to use both tools.
- **Security Audit:** focused review of backend-only credentials, Git/ZIP exclusions, localhost/origin/private-marker checks, bounded inputs and any changed code. It is a review, not a claim of a completed penetration test.
- **Graphify / skillspector / Agent Skills / Superpowers:** use only if verified and they reduce the actual task; do not make graph generation or tool installation a graduation prerequisite. Inspect REA's real description before assigning it a role.
- **Pro Design / Impeccable / Replica:** defer redesign. Use only a small accessibility/usability fix needed for the existing demo or a consistent final document layout. Do not clone another site's branding/assets or replace the native analytics core.
- **Human / humanizer:** optional clarity editing, preserving facts, numbers, citations, student voice and an accurate AI-assistance/contribution description. Do not invent personal experiences or claim detector evasion/watermark removal. The pasted watermark guide is unrelated source material, not instructions to install it or hide authorship.
- **GitHub / Engineering:** if connected and authorized, inspect diffs and publish only project files after privacy checks. Otherwise use existing Git or prepare a local checkpoint and say what was not pushed. Never print credentials or silently change global settings.
- **Firecrawl / Perplexity:** optional source discovery only; use accessible primary papers/official documentation when these are unavailable. Do not request keys in chat, upload private data to third parties, or let an optional connection block local work.
- **HyperFrames:** optional; the required output is an editable PPTX, not a new video or sign-in workflow. No new animation/video scope is needed.

Use the simplest suitable available document/PDF/presentation capabilities. If a format cannot be opened/exported in your environment, preserve the source, finish independent work and give me one exact manual action. Never claim a native HWP conversion, render, browser check or installation succeeded without observing it.

## 4. Current implementation: inspect and preserve

Recorded program version **0.6.0** includes:

- Riot ID lookup, regional routing, completed ranked-match history/detail/timelines, current rank/mastery, backend-only keys, paced requests, caching and explicit partial/error/demo states.
- Genuine-match ingestion/deduplication, refreshed native statistics, history pagination, full ten-player scoreboards, lane-opponent comparisons, shares and gold timelines.
- Items/runes/spells, observed purchase/sale/undo histories, normal skill orders, champion/role/patch/queue aggregates and recent role/champion profiles.
- Own explainable post-match tips, private manual feedback, persisted practice targets, dated current-rank snapshots and previous-lookup history.
- JSON model inference, original MLP/logistic evidence, separate temporal models, feature sensitivity, comparison/audit panels and analysis export.
- Optional official OP.GG MCP data/workbench and verified KR historical-rank archive API; actual YouTube metadata lookup with honest date/view/patch-text labels.
- English/Korean switching. A limited own-player Live Client reader exists, but actual in-game acceptance is deferred.

Our tip formula is `priority = gap × equal_descriptive_weight × recency_weighted_consistency`. It uses same-role/patch/queue references, excludes the selected player and loaded matches, and requires 30 reference games, ten distinct reference players and three recent observations per metric. Details and tests are in `tips_engine.py`, `tips_config.json` and `docs/TIPS_ENGINE.md`. Do not substitute the serving team's model weights for learned player-skill impacts or label local percentiles as server-wide rankings.

## 5. Unfinished features: make the scope honest

Audit each significant requested feature as implemented, partial, missing, deferred or blocked, with a source/test reference. Do not blindly label an older missing item as missing without checking newer code.

Known unfinished work includes learned player-metric impact weights/SHAP, sufficient tier benchmarks, the separate current-rank-at-fetch estimated-tier/lobby-enrichment pipeline, a usable low-elo study, authenticated peer feedback, communication/behavior classifiers, statistically validated item/strategy advice and coaching efficacy. Full OP.GG/YOUR.GG/FOW/GGQ/DEEPLOL parity is not complete. A dedicated archived-rank UI is also deferred. Public production hosting/authentication/load validation and clean-machine installation have not been verified.

Do not silently broaden strict prospective historical-rank labels to estimated present-day labels. Any later estimate mode must be separate, dated and clearly identified. Do not infer manners, intent, AFK or skill tier from unsupported metrics. The current build's descriptive item frequencies and retrospective item-choice coverage are not evidence of optimal purchases.

Complete only deadline-critical defects and bounded missing pieces needed for the agreed demo. Keep larger research/product features in a clear later backlog, with no invented results or promise of future autonomous work. Do not start a real game or a voice coach during this wrap-up.

## 6. Research facts that must stay exact

Original frozen data: **104 unique genuine KR matches, chronological 83 training / 21 later holdout**, already inspected and exploratory. Serving MLP: **6→16→8→4→1, 289 parameters**, training accuracy **95.18%**. Original holdout:

- MLP: accuracy **47.62%**, ROC-AUC **0.490909**, Brier **0.372683**.
- Logistic: **57.14%**, **0.609091**, **0.263561**.
- Exploratory RF: **66.67%**, **0.590909**, **0.260681**; not installed as serving model.
- Constant prior: **47.62%**, **0.5**, **0.259862**.

Inputs are six early **team differences**: gold, XP, CS, kills, towers and dragons. The last complete frame in a 9–10-minute window is used; actual original frames are about **9 minutes**, not exact 10:00. Do not let final-game fields leak into historical prediction inputs.

Separate later-period audit: frozen unchanged models/exclusions, a **180-game collection snapshot**, **35 later eligible games**, retrospective convenience sampling. MLP **57.14% / AUC .67 / Brier .319481**; logistic **80.00% / .873333 / .168850**; constant **42.86% / .5 / .267321**. No retraining or replacement was performed. Different samples do not prove improvement; the neural model is not superior and has worse Brier than the constant/logistic baselines. Eleven time-specific MLPs are independent window models, not an LSTM or independent evidence per timepoint.

The separate collection reached **185 genuine games at the last verified snapshot** and may grow on lookup. It is not the training count. Saved low-elo evaluation had **zero enrolled players / zero eligible games**. The lost **1,000-game, 10,000-player-row, XGBoost 79% / AUC .86** experiment remains reported history without recovered files. Never report it as reproduced current work.

Preserve the frozen JSONL, model parameters, evaluation plan, raw stores and earlier academic copies. Read their hashes/provenance in the handoff. **Do not retrain over the active model, tune on a viewed holdout or use the collector's default output to append to the frozen JSONL.** If later authorized research needs new data/models, use new explicit paths and a fresh protocol.

## 7. Finish academic materials against the actual requirements

Latest reviewed files are in:

```text
submission/final_v06_2026-10-30/
  LolAi_FinalReport_v06_Review.docx
  LolAi_FinalReport_v06_Review.pdf
  소프트웨어학과_박승현(2019310202).pptx
```

The report is **46 pages**, the PPT **18 slides**. Both were visually checked. The report is a Word/PDF reconstruction of the supplied form, **not a native HWP file**. Original template:

```text
C:\Users\sh Park\Downloads\연구논문작품_최종보고서.hwp
```

I confirmed free-format slides are acceptable. Do not treat sample screenshots as proof of the actual school track or completed uploads.

Prioritize these outstanding gates:

1. Verify the exact registered title and align cover, PPT and portal metadata. Current strings differ, notably whether “리그 오브 레전드” appears. Do not invent the approved title.
2. Confirm accepted final-report file format and adviser/online-signature requirements. Keep scores/signatures blank for authorized people. Prepare a checked native-format revision only if required and supported.
3. Have me verify personal reflection, contribution/AI-assistance description, dates and student/college metadata. Ask only facts the files cannot establish; continue unrelated work meanwhile.
4. Audit the form's page guidance. Current related work is about **two pages** versus its approximate **seven-page** guide; total report is longer than its approximate 30-page guidance. These are guide comparisons, not established automatic rejection rules. Improve meaningful methodological discussion if appropriate/time allows, without padding or pretending to have read inaccessible full papers.
5. Preserve at least **three Korean and three English research references with numbered in-text citations**. Check `KOREAN_RELATED_WORK.md` and `ENGLISH_RELATED_WORK.md` for verified sources/access limits; verify new scholarly claims using primary sources. Never fabricate references, DOIs, experiments or claimed performance.
6. Keep report abstract, implementation, figures, results, limitations, conclusion, source appendix and PPT consistent with the final actual code and measured evidence. An honest negative neural result is acceptable to describe; only the adviser can decide whether it meets the graduation standard.

Save edits as a **new revision**, preserve the current reviewed originals, update contents/captions/page numbers and render/check the new report and all affected slides. Retain an editable DOCX/PPTX and checked PDF when accepted. Use original explanatory figures instead of excessive screenshots. Add a short demonstration script and truthful likely-Q&A notes if existing versions need updating.

## 8. Test the result without disrupting the working demo

From the project folder, existing Windows commands are:

```powershell
.\start.cmd
.\check.cmd
```

Keep the server terminal open; use a separate one for checks. App: http://127.0.0.1:8000. Prefer `.cmd` because direct `.ps1` execution was blocked by the user's policy. Do not weaken global execution policy. Restart only when backend/config changes require it. Inspect existing setup and dependencies before reinstalling anything.

Frontend, from `frontend`:

```powershell
node --test tests/resources.test.mjs tests/profile-review.test.mjs tests/i18n.test.mjs tests/research-tools.test.mjs tests/native.test.mjs
pnpm run build
```

There is no `npm test` script. Recorded results are **276 backend tests + six subtests, one warning; 41 frontend helper/static-render tests; TypeScript/Vite passed**. This is historical evidence until you rerun it. The earlier restricted environment had socket/DNS failures while the user's normal Cursor terminal/browser worked; distinguish environment failure from app failure.

After relevant code changes, run appropriate checks and fix genuine failures. For final acceptance, check demo and genuine/cached lookup if available, source labels, history/detail, own tips and sample gates, practice persistence, export, English/Korean, missing credentials/upstream errors and absence of browser console/runtime errors. Use localhost only. Do not invent a live result when unavailable; record the exact limitation. Preserve private data and remove only your disposable test records. Do not claim a unit-test pass is an independent model validation or a completed security audit.

## 9. Package, publish and prepare submission

Create a new clearly named final candidate containing source/run instructions, publishable models/aggregate results, report/PPT/PDF, demonstration steps, test receipts, citations, limitations and a manifest of files/hashes. Preserve older ZIPs. Ensure the package is actually runnable with documented setup limits; public source alone cannot reproduce experiments requiring excluded raw data.

Keep `RIOT_API_KEY` and `YOUTUBE_API_KEY` only in ignored local `backend/.env`. Never print, commit, paste into the report, or request credentials in chat. Inspect the final ZIP/Git diff for secrets and private files. Exclude `.env`, private raw JSONL/SQLite, private notes/rank stores, certificates, caches, dependencies and office files. Keep source labels and numerical artifacts intact.

Private backup `.private-backups/20261030T095835552204Z` contains 14 verified files including the 185-game store and original research data. It remains local unless an off-computer copy is actually confirmed. Prepare/check a new private snapshot if changes require it, and ask for an owner-controlled private destination only when necessary; do not publish raw data on the public repository. Maintain the public manifest when publishing updates. Preserve user changes and report the actual commit/link; do not claim a push based on a local commit alone.

Prepare exact files and a short portal checklist for report, project/paper deliverable and presentation. Paper-track conference evidence is a separate conditional requirement; do not invent it or confuse its December date with today's final deadline. Show me the finished candidate, remaining issues and exact files before any final school submission. If I explicitly approve that concrete upload, use the available authorized route; otherwise leave me ready to upload. I type login credentials myself. Never send email/contact the adviser or department, sign, assign scores or declare upload success without authorization and observed confirmation.

## 10. How to work and what to deliver

Start with a concise verified state and the most urgent remaining work, then act immediately. Do not ask me to repeat information already in the handoff. Ask one clear question only when a necessary fact/decision is missing, while continuing independent work. Do not block on optional API keys/plugins or require three writing samples before editing the report. Keep changes small and explain material risks. If using parallel agents, assign separate files/tasks and review merged diffs; avoid concurrent writes to the same file.

Keep a concise `docs/WRAP_UP_STATUS.md` recording actual files changed, checks with outcomes/time, remaining human gates and the next action. Create it only as the working wrap-up record, not as another duplicate roadmap. Update the handoff if current evidence changes.

At the end provide:

- Exact final file paths/download links, editable sources and the new candidate ZIP.
- What works, what is partial/deferred, and any unresolved defect or academic gate.
- Actual test/build/browser/render results, separately from earlier receipts.
- Exact launch/demo steps and GitHub publication state.
- Honest model/dataset/validation limitations and AI-assistance/contribution wording for my review.
- A short “what I need to do now” checklist and submission confirmation only if an authorized upload actually succeeded.

Finish all work within the agreed feasible submission scope in this active session. Do not call the original full product vision “100% complete,” promise guaranteed graduation acceptance, claim an unrecovered experiment was recovered, or imply future autonomous work will happen after the session. If only a student/adviser/portal action remains, state that exact dependency and leave the concrete reviewed package ready.

**Begin by reading the files and checking the current state. Then perform the first useful deadline-critical task.**
