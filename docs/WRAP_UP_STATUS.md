# Wrap-up status: October 30, 2026 (Asia/Seoul)

Checked in the final Claude Code session, starting 22:32 KST. This file is the current status. Older handoff and README paragraphs are dated history.

## Actual changes

- Application code: **none**. Version stays 0.6.0. The checks below found no defect to fix.
- Report: new `submission/final_v07_2026-10-30/LolAi_FinalReport_v07.docx` and `.pdf` (47 pages).
  - Cover title now matches the slides and the working title in `docs/SUBMISSION_REQUIREMENTS.md`.
  - Related work gained one comparison table and two paragraphs, using only what `docs/KOREAN_RELATED_WORK.md` and `docs/ENGLISH_RELATED_WORK.md` record as verified.
  - One process sentence about review copies was removed from the conclusion.
  - Contents page numbers were refreshed and checked against the printed page numbers.
- Presentation: unchanged from the reviewed 18-slide file, copied into the v07 folder.
- Documents: this file, likely presentation questions in `docs/DEMO_SCRIPT.md`, and the v07 `READ_ME_FIRST.md`.
- The reviewed v06 files, the frozen dataset, the active models and the blank HWP form were not modified.

## Checks and outcomes

| Check | Result |
|---|---|
| Backend tests | 276 passed, 1 warning, 6 subtests passed in 28.70s |
| Frontend tests | 41 of 41 passed |
| TypeScript and Vite build | Passed (`tsc --noEmit`, `vite build`) |
| Health endpoint | 0.6.0, Riot key configured, no key in the response |
| Sample demo | Loaded, labeled as synthetic, gives no real-player benchmark |
| Live lookup, Molybdite#KR1 | 10 matches, labeled as connected to Riot API |
| History paging | Offset 0 to 10 returned 200 |
| Own tips | Showed 159 and 161 reference matches and the ten-player rule |
| Practice | Save 201, reload 200, delete 200; test target removed, 0 targets stored |
| Export | `lolai-live-analysis.json`, about 689 KB, no key pattern |
| English/Korean switch | Korean interface shown and saved; switched back |
| Browser console | No errors |
| Private backup | `.private-backups/20261030T134001046635Z`, 14 verified files |

Report checks: rendered with Microsoft Word, changed pages inspected, and every contents entry matched its printed page. v06 and v07 text differ only on the cover, contents, new related-work page and conclusion pages.

Not checked: real in-game connection, a clean new computer, production hosting, the missing-key screen in a live browser (covered by automated tests only), or a penetration test. No code changed, so no security review of new code was needed; the package was scanned for key patterns and private data files.

The private collection is now 187 genuine matches after the live lookups. It is separate from the frozen training data. The frozen JSONL and both active model files still match their recorded SHA-256 values.

## Feature status

| Status | Features |
|---|---|
| Implemented | Riot ID lookup, ranked history, details, timelines, paging, ten-player scoreboards, lane comparisons, gold timelines, item and skill histories, champion/role/patch aggregates, own tips engine, private practice and notes, rank snapshots, neural and baseline inference, evaluation panels, JSON export, YouTube metadata lookup, English/Korean switching |
| Partial | Provider support (OP.GG archive API has no website card; other providers are links), own-player Live Client reader (not tested in a real game), tier benchmark code path (no usable cohort) |
| Missing | Learned metric weights or SHAP, participant estimated-tier enrichment, validated item or strategy advice, authenticated peer feedback, communication or behavior classifiers |
| Deferred by the owner | Visual redesign, voice coaching, large real-time coaching, real-game testing, statistical skill-rank estimation |
| Blocked | Low-elo study (zero enrolled players, zero eligible games), coaching efficacy (needs a real user study), public deployment and clean-machine checks |

## Remaining human gates

1. Compare the title with the portal. The report and slides use: **LolAi.gg: 딥러닝 기반 리그 오브 레전드 과거 경기 분석 및 승패 예측 시스템**. This is the working title, not a confirmed registered title.
2. Confirm the accepted report format. The report is DOCX/PDF, not native HWP.
3. Read and correct the reflection and the AI-assistance wording.
4. Confirm department, college, project or paper track, and individual status.
5. Delete the first GitHub token if that is not done.
6. Complete the adviser review and online signature.
7. Upload the files and keep the portal confirmation.
8. Copy the private backup to an owner-controlled place off this computer.

## Next concrete action

The student opens `submission/final_v07_2026-10-30/READ_ME_FIRST.md` and follows the upload checklist before 23:59 KST.
