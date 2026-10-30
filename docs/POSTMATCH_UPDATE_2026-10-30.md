# Post-match learning update — October 30, 2026

The user deferred actual-game testing because League cannot be run in the current situation. The live connection was stopped; the feature remains available for a later, user-initiated check. No active match, live coaching success or coaching benefit is asserted.

This increment changes the frontend only. Backend 0.3.0, its user-confirmed **154-test/six-subtest pass**, the raw dataset and model weights remain unchanged. No server restart is required; refresh the app.

## Changes

- **Readable historical items:** same-champion/role/patch inventory counts now show official Data Dragon item names and icons in English or Korean. The app finds an available Data Dragon build for the exact match patch, shares requests with the existing resource panel, omits credentials and retains IDs/counts when labels are unavailable. It never substitutes a different patch. These remain final-inventory observations, not purchase-order or item-efficacy evidence.
- **Normal matchup form:** connect OP.GG, enter an opponent champion and select **Load matchup guide**. It uses the selected match's champion/role, the current UI language and the actual `lol_get_lane_matchup_guide` schema. There is no lobby reading or inferred opponent. Its API does not support the build form's tier filter or a historical patch argument; the UI states this explicitly.
- **Actual provider guide:** observed both English and Korean Sylas-versus-Warwick jungle responses through the running backend. The guide displays the provider's own champion/opponent identity, text, play-style/advantage fields, source and fetch timestamp. Missing written tips remain missing. External advice is not converted into a personal model prediction or a claim of validated improvement.
- **Provider result compatibility:** both compact single-build records and array-valued matchup results are supported. Repeated builds are deduplicated. Up to three core builds and one starter/boot choice are displayed by provider pick frequency and sample count, never by selecting the largest observed win rate. Counts and the observational caveat remain visible. Remote text is parsed as data or displayed as plain text; it is not executed or rendered as HTML.
- **Feedback safeguards:** deleting a note now requires a separate explicit confirmation, with a cancel option. A missing-note 404 is reported as a missing note, rather than telling users to restart the backend. Malformed non-object API replies fail with a readable error. No real peer feedback, fabricated ratings or human consent records were created during this check.

## Observed checks

**30 frontend tests passed**, along with TypeScript and production Vite build. New checks cover exact historical-version selection, safe CDN image URLs, localized/shared metadata requests, absent patch handling, array-valued provider records, frequency-based ordering, malformed guide identities, excessive guide text and correct 404/error reporting.

In the real browser:

- Genuine Molybdite#KR1 analysis still loaded, with selected Sylas game `KR_8437811854`.
- The ten-match training group kept the same counts: 3152 in 9/10, 3020 in 7/10, 3157 in 4/10 final inventories. They displayed Hextech Rocketbelt, Sorcerer's Shoes and Zhonya's Hourglass in English, and official Korean names after switching language. All three icons loaded from Data Dragon **16.21.1**.
- The normal matchup form returned a genuine OP.GG guide for Sylas versus Warwick in Jungle. Korean querying returned Korean provider prose and champion names; the surrounding interface and item labels also translated.
- No game connection was started for this update. The existing prospective low-elo report remains **0 eligible future matches / 0 enrolled players / no metrics**.
- Responsive checks at 390px and 1280px produced one and two columns respectively, with no horizontal document overflow. The temporary viewport override was reset. English was restored, an English guide reloaded, and the live connection remained off.

Software checks and provider responses do not establish that these tips improve a player's outcome. Original lost experimental data/results are still unrecovered. FOW/GGQ/DEEPLOL remain external links pending documented authorized data access. Verified peer participation, prospective low-elo evaluation and real-game telemetry are still open.

## Use it now

1. Refresh the running app and analyze a completed real match.
2. Review named items in **Item evidence and low-elo validation**.
3. In **Connected provider data**, click **Connect OP.GG**, enter an opponent and click **Load matchup guide**. The existing build button and tier filter remain available independently.
4. Switch to Korean if desired, then query again to request Korean provider content. Changing the UI language does not pretend that previously loaded external text has been translated.

No additional API key, game session or backend restart is needed for these post-match tools. Existing report/PPT review copies predate the provider/research-tools increments; this note is a verification supplement, not a new official submission or adviser approval.

Primary references: [Riot Data Dragon items, versions and localization](https://developer.riotgames.com/docs/lol), [official OP.GG MCP tools](https://github.com/opgginc/opgg-mcp).
