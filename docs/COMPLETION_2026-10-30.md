# LolAi.gg 0.6.0 implementation and evidence

## Current program

Backend 0.6.0 is running locally. The user supplied the full normal-terminal
result: **276 passed, one warning, six subtests passed in 32.90s**.
[Full receipt](QA_FULL_BACKEND_0_6_0_2026-10-30.txt). Restricted-session regression
separately passed 246 tests and six subtests; 41 frontend tests, TypeScript and
production build passed. No new dependency was installed.

The original 104-game research JSONL, installed MLP and original evaluations
remain unchanged. Separate automatic collection reached **180 genuine matches**
for the audit snapshot and **185 matches** after live acceptance. These counts
are collection sizes, not new training-set sizes.

## Implemented in this increment

- `loadout_timeline.py` reconstructs observed purchase, sale, consumption,
  undo and normal skill-level histories. It retains event timestamps and known
  reversals, preserves legitimate identical purchases, and ignores repeated
  frames. Ambiguous undo records are visible but excluded from purchase-order
  aggregates. Missing, invalid and incomplete timelines never become complete
  evidence. Evolve events are not normal skill-point choices.
- Native champion groups now separate final inventories from the first six
  observed purchase/skill choices, with their own usable-record denominators.
  Existing SQLite catalogs rebuild once for computation version 2. At the
  initial 180-game snapshot there were 440 groups, 1749 usable purchase
  player-game rows and 1800 skill rows. Frequencies are descriptive; no optimal
  build, purchase causality or recommendation efficacy is claimed.
- Explainable tips additionally require **ten distinct reference players** per
  metric, alongside 30 separate matches. They report distinct players and metric
  coverage. The existing gap × equal weight × consistency formula, role/patch/
  queue filtering, self-exclusion and minimum recent-game rules remain. Weights
  are still descriptive, not learned player-level win impacts.
- Private server-side practice targets freeze a baseline of 3–10 earlier
  completed same-role, patch and queue games. Only the first three later stored
  games qualify. Baseline IDs and averages persist in SQLite; changes never
  backfill the baseline. Four supported goals are CS/min, vision/min, kill
  participation percent and deaths. The UI supports save, reload and confirmed
  deletion. Existing browser-local targets remain available separately.
- `/api/practice` GET/POST and `/api/practice/{id}` DELETE use the existing
  localhost/origin/private-marker boundary and a player-hash namespace.
  This is a private single-user notebook, not Riot Sign-On ownership proof,
  authenticated peer testimony or a public reputation system.
- Previous/next history controls use the loaded player's identity and paging
  metadata, preserve cancellation/version checks and label statistics as
  page-specific. A new game can shift Riot history offsets between requests.
- The fixed-model later-period audit is available via
  `/api/model-validation` and its English/Korean panel. A report for another
  model hash is rejected. No metrics are displayed until at least 20 qualifying
  games with both outcomes exist.
- `backup-private.cmd` creates a new private backup folder using consistent
  SQLite backups and per-file SHA-256 checks. It includes original raw data,
  collection/notes/rank stores, models and research artifacts, while excluding
  keys and expiring response caches. Private backups are ignored by Git and
  excluded from source/review ZIPs.

## Additional 35-game audit

Before additional collection, saved MLP and logistic model copies/hashes and the
108 already collected or reviewed IDs were fixed in
`backend/data/later_validation_plan.json`. The original training and viewed
holdout IDs are necessarily excluded. Games must start after both model files
were created. The MLP's original hash remains
`9a64650a4dade3b14c0370c999df8573b36da524cd6a413dee9b492a6cee017e`.

Sampling used the first three other nonempty public Riot IDs, in participant
order, from one stored seed match; their newest ten ranked games each were
requested. Eight games passed the audit filters, below the fixed minimum 20.
Before calculating model performance, collection was expanded once to the
remaining six other players in that same roster. No players or games were
chosen for a favorable prediction or outcome.

The resulting collection snapshot had **180 unique games**. The audit excluded
108 prior/reviewed games and 37 games predating the frozen models, leaving
**35** games: 15 blue wins and 20 red wins. Each game supplies one blue-side row.
There were 316 distinct participants, three also present in the original
snapshot. Results, calculated at 2026-10-30 18:12 KST:

- Unchanged MLP: **20/35 = 57.14% accuracy**, ROC-AUC **0.670000**, Brier
  **0.319481**.
- Unchanged logistic baseline: **28/35 = 80.00%**, ROC-AUC **0.873333**, Brier
  **0.168850**.
- Constant original training prior 48/83: **15/35 = 42.86%**, ROC-AUC **0.5**,
  Brier **0.267321**.

These are a **retrospective later-period convenience-sample audit**. The protocol
was chosen retrospectively, and roster-based recruitment and repeated players
limit independence. It is not independent external validation or a coaching
trial. The MLP still has higher probability error than the constant prior and
logistic regression. The original 21-game and additional 35-game samples differ;
their accuracy difference is not evidence that the model was improved. No model
was fitted, selected or installed as a replacement in this increment.

Private plan and summary reports are in the ignored data directory; the private
backup includes them. The aggregate summary can be included in review packages.
Exact reproduction also requires the private raw collection. Later live lookups
may grow the store without changing this dated 35-game report.

## Live acceptance

- Health reported **0.6.0**, correct source labels and coherent dataset revisions.
- Real Molybdite#KR1 analysis returned ten matches. A selected Sylas history had
  **40 item events, 21 non-reversed purchases and 15 normal skill choices**, with
  no unresolved undo. Item labels came from the existing historical Data Dragon
  metadata path, and displayed times matched the API records.
- Genuine jungle tips showed 157–159 reference games and 278–282 reference
  players per displayed metric, full reviewed-metric coverage, and the explicit
  ten-player minimum. No historical rank was inferred.
- The application moved from demo offset 0 to 10 and back to 0; genuine-player
  lookup then worked. Demo records never entered the genuine collection.
- One disposable private target was saved with a ten-game baseline, survived a
  full app reload and was loaded again. It correctly had zero later games.
  It was deleted through the UI afterward; SQLite confirmed **zero temporary
  targets remaining**. No improvement result was fabricated.
- The later audit displayed all three MLP metrics and the logistic comparison.
  Korean switching preserved values and translated the new explanations.
  Screenshot: `docs/screenshots/v06-later-audit.png`.

The user supplied a native Word PDF. All 46 pages were rendered and inspected;
the contents page was then fully refreshed to include section 8. A separate clean
review DOCX/PDF was saved, keeping the supplied draft/PDF intact. All changed
pages were inspected again and unchanged pages matched pixel-for-pixel.
The report keeps the original 21-game experiment separate from the additional
35-game audit. Personal reflection editorial instructions were moved out of the
report; the student must still verify that the wording reflects their experience.
The 18-slide presentation was rendered, inspected and validated, including the
college label beneath the student's name, native tables/charts and original
research results. Latest report and slide copies are in the sibling
`submission/final_v06_2026-10-30` directory. Visual verification is not academic
approval or school submission.

## Remaining boundaries and handoff

Authenticated public peer feedback, learned player-level impact weights,
sufficient verified tier/low-elo cohorts and coaching efficacy remain research
work. Statistical skill-tier estimation, voice/live coaching and visual redesign
remain deferred. The lost original experiment is not recovered. No all-features
clone of OP.GG/FOW/GGQ/DEEPLOL/YOUR.GG is claimed.

The latest private backup is
`.private-backups/20261030T095835552204Z` (14 verified files). It contains the
185-game collection after the temporary test target was removed. It remains on
this computer; copy it privately to an off-computer destination. No cloud upload
or off-computer backup has been verified.

The new report and slides are review copies. Student reflection/contribution
review, accepted report file format, adviser review/online signature and the
actual school upload remain human steps. The stated deadline is **October 30,
2026 at 23:59 KST**. No signature, score or school submission was performed.
The GitHub source/review publication is tracked separately in `GITHUB_BACKUP.md`.
