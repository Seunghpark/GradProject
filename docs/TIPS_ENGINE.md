# LolAi explainable review priorities

This is LolAi's own deterministic, post-match prioritization formula. It does not call an LLM or an external analytics site. It is a project design contribution, not a claim that this formula is novel across research or that following it improves win rate.

Implementation: `backend/app/tips_engine.py`. All display thresholds and metric directions are in `backend/app/tips_config.json`.

## The formula

For metric j, use the average of its available values in up to ten recent eligible games. Only the latest loaded role/patch/queue cohort is considered; at least three recent observations of a metric are required.

1. Let P be the metric's **performance percentile** in the eligible reference rows. Tied values receive their midrank: `(number below + 0.5 × number equal) / reference rows`. For early deaths, reverse the percentile, because lower is the favorable direction.
2. `gap = max(0, (50 − P) / 100)`.
3. `weight = 1 / K`, where K is the number of metrics with enough reference and recent data. These are explicitly **equal descriptive weights**, not learned win-impact weights.
4. For the most recent game, r=0; for each older game, increment r. `recency_weight = 0.85^r`.
5. `consistency = sum(recency_weight for games on the unfavorable side of the reference median) / sum(recency_weight for all available metric observations)`.
6. `priority = gap × weight × consistency`.

Example: a performance percentile of 20 gives a gap of 0.30. With two usable metrics, weight=0.50. Weighted consistency of 0.80 produces priority=0.12. These numbers rank review topics; 0.12 is not a win-probability change or an estimated causal effect.

Display up to three positive priorities, in descending order with deterministic metric-name tie breaking. Display one relative strength if at least one eligible metric reaches the midpoint. Do not invent three weaknesses or a strength when the evidence does not support them. The UI displays actual average, median, percentile, observed frequency, reference size and formula factors for each tip.

## Reference rules

- Build from the local Riot JSONL records, deduplicating match IDs. Keep synthetic and genuine provenance separate.
- Compare the same role, major/minor patch and ranked queue. Do not pool solo and flex.
- Exclude **every loaded match** and **all rows belonging to the selected player** from references. The internal benchmark artifact stores a one-way PUUID digest for this exclusion; raw PUUIDs and names are omitted from it. The artifact is not returned by an API route.
- Require at least 30 distinct reference match IDs **for each metric**. Thirty is an MVP display gate, not statistical validation. Two same-role participants can contribute rows from one game; they are not independent games.
- Use champion-specific references only when all reviewed games use the same champion and that champion cohort contains at least 50 separate matches. Otherwise fall back to the same-role cohort, explicitly identified in the UI.
- Missing values remain missing. Do not turn absent timelines, ward counts or objective assists into invented observations.
- The configured fallback-threshold dictionary is empty. No purported universal Gold, low-elo or coaching threshold is silently substituted.

The initial frozen reference artifact contained 104 unique Riot matches / 1,040 player-match rows and **zero tier-labeled rows**. Runtime references can refresh from the separate genuine match store; they do not change the frozen model experiment. Repeated players, convenience sampling and limited patches prevent interpreting its percentiles as server-wide rankings. References can be earlier or later than a reviewed match; this is retrospective review, and no tip statistic enters the historical prediction model.

## Metrics and their limits

Current candidates: CS/min; early CS and same-role gold difference from the latest complete available role pair in minutes 9–10; same-role gold difference in minutes 14–15; kill participation; damage share; vision/min; wards placed/min and cleared/min; recorded deaths before minute 14; recorded major-monster kill/assist participation.

The exact selected snapshot time is available in the full match review. An early snapshot is **not relabeled as an exact 10:00 value**. Early-death counts are omitted when a match ended before 14 minutes. Objective participation is omitted without a matching timeline or when the team's available timeline has no recorded major-monster kills. Assists may be incomplete. Damage-taken share is displayed as a neutral match statistic but excluded from tip priority because more is not consistently better. CS and damage-share priorities are omitted for support.

Each metric has a fixed action template asking the player to inspect a replay decision. These templates are review prompts, not an inferred diagnosis, optimized item purchase, hidden behavior score or automatic in-game instruction.

## Tier mode: implemented, data not yet available

`generate_tips(..., scope='role_tier', tier='GOLD')` uses only that reference tier and returns `tier_unavailable` or `insufficient_data` when evidence is missing. This mode does not guess a tier for the selected player. The current UI does not offer an active tier selector because there is no usable tier cohort.

`build_benchmarks(records, rank_observations)` accepts the existing rank-enrollment record format. A label requires `source=riot_rank_at_enrollment`, matching PUUID/platform, solo queue, a valid Riot tier and an observation timestamp **before** the match start and no more than 30 days old. A current rank observed after an old match is rejected. The label means rank observed at enrollment, not proof that rank stayed unchanged throughout that interval or that all lobby players shared that tier. Observation collection must remain fresh rather than restamping cached ranks.

The existing enrollment CLI supports the prospective Iron/Bronze/Silver study; it does not yet collect broad Gold-to-Challenger benchmark cohorts. No actual tier-comparison result is claimed.

## Learned importance is not implemented

The lost XGBoost experiment and its claimed historical results have not been recovered. The active MLP uses six **team-difference** features, not this collection of player-review metrics. Its weights or sensitivities cannot honestly be reused as role-specific causal impact weights. The current formula's JSON field `impact_weight` is an equal placeholder, and the UI names it accordingly. A later learned-weight extension needs suitable player-level training data, a documented fitting method and separate validation; SHAP is not currently used.

## Rebuild and check

From the project folder:

```powershell
.\.venv\Scripts\python.exe backend\scripts\build_tip_benchmarks.py
.\.venv\Scripts\python.exe backend\scripts\build_native_catalog.py
.\check.cmd
```

An optional `--enrollments PATH` supplies previously collected rank observations. Default outputs are ignored local JSON artifacts. Source records and model weights are preserved. Analysis cache keys include the benchmark/config version so a rebuild invalidates old tip payloads.

Tests cover exact arithmetic, ties and inverted metrics, recent weighting, unique-match minimums, self/match exclusion, role/patch/queue separation, champion fallback, provenance separation, rank freshness and future-rank rejection, missing inputs and English/Korean display. These establish implementation behavior, not coaching efficacy.
# 0.6.0 evidence update

Each usable metric now additionally requires ten distinct reference player
digests, alongside the existing thirty separate-match minimum. Outputs include
reference-player counts and reviewed-metric coverage; they do not claim formal
statistical certainty. Equal descriptive weights remain unchanged. Persistent
same-role/patch/queue practice targets now measure the first three later stored
games against a frozen 3–10-game baseline, with no causal efficacy claim. See
[the validation record](VALIDATION.md).

