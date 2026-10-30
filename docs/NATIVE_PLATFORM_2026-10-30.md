# Native LolAi platform — backend 0.4.0

The user clarified that LolAi should itself provide the core workflow inspired by OP.GG, YOUR.GG, FOW and GGQ. External service links and queries are supporting resources. This increment implements native Riot-data features; it does not claim feature parity with those services or access to their proprietary scoring models.

Implemented:

- Full ten-player role-ordered scoreboard, selected-player highlighting, per-team kills/gold/objectives, item slots, recorded loadout IDs, damage and gold shares. Missing optional records display as unknown.
- Same-role opponent comparison using actual timeline snapshots in minutes 9–10 and 14–15; early CS, gold/XP/CS differences; recorded early deaths, major-objective kill/assist credits and death-before-objective replay markers. Timing alone does not establish an avoidable death or blame.
- Native champion explorer: 104 local Riot matches, 279 champion/role/patch/queue groups. Search/filter by champion, role, patch, queue and minimum sample; observed item frequencies, complete final inventories, rune IDs and role-opponent results. Official Riot Data Dragon supplies item display metadata only. These are small-sample observations, not global tiers or optimal builds.
- Latest-five versus previous-five same-role trends, and a browser-local practice target checked against up to three genuinely later loaded games. Existing loaded games are excluded. Targets are player-selected, not demonstrated interventions.
- The standalone explainable tip formula and its reference/config modules, with English/Korean UI. See `TIPS_ENGINE.md` for exact arithmetic, available versus unavailable modes, metric caveats and tests.
- Optional references/research section is closed initially and mounts its external guides and research tools only when opened. The native core does not require any third-party analytics provider. Experimental live polling remains off by default; actual-game testing is deferred at the user's request.

Validation recorded before browser handoff: 153 backend tests and six subtests pass in the restricted session, excluding 27 API/collector tests requiring the normal Windows terminal. All 38 frontend tests, TypeScript and Vite production build pass. A genuine-record offline analysis returned native scoreboards and an available tip backed by 83 excluded-player/loaded-match reference games. The active model and raw dataset hashes remain unchanged. Fresh browser verification and the full normal-terminal suite must be recorded separately; the older 154-test receipt applies to backend 0.3.0 only.

Still incomplete: service-wide champion/rank coverage, validated item or strategy efficacy, learned player-metric impact weights, actual tier benchmark data, authenticated peer validation, the prospective low-elo study, recovered original experiment and production hosting. Voice coaching and other large real-time features are outside this MVP.

Run the existing server with `start.cmd`, then open `http://127.0.0.1:8000/`. Use a genuine player in **Live Riot API** mode to see eligible local-comparison tips. The synthetic demo intentionally does not compare fictional players with real benchmarks. **Champions & builds** opens the independent local explorer. English remains the default; Korean is a saved explicit preference.

The preserved final-report DOCX and PPT are earlier review copies; this source increment does not silently update their content, adviser approval or official submission status.
