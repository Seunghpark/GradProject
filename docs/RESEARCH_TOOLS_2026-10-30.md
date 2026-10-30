# Research tools, version 0.3.0 — October 30, 2026

This increment implements a bounded research pilot. It does **not** complete the whole OP.GG/FOW/GGQ/DEEPLOL feature merge or establish that recommendations improve players' results. The lost original experiment is still unrecovered. Existing raw data and the active neural-network artifact were preserved byte for byte.

## Implemented and observed

- **Official OP.GG data:** backend discovery and allowlisted calls to `https://mcp-api.op.gg/mcp`, using its actual runtime schemas. Champion analysis, item metadata and lane matchup guide tools are allowed; arbitrary tools/hosts are not. The browser verified actual Bronze Ahri build data: core items Malignance/Shadowflame/Zhonya's Hourglass, 6,120 provider games, 3,232 wins, 18% provider pick rate. These are conditional provider statistics, not an estimated treatment effect. Build cards preserve names, IDs, counts and requested tier. Provider region and build patch scope are not independently established; the API has no historical patch input in its current champion schema. The raw response's trend entry was patch 16.21. A bounded, non-executing compact-data parser handles its class/constructor-style output; unsupported data remains plain text. Advanced schema-based querying remains available.
- **Local item evidence:** minimum five earlier matches with the same champion/role/patch. Counts describe final inventories, excluding trinket slot 6. This does not establish purchase order or situational suitability. No build is substituted for unsupported groups. Genuine Molybdite#KR1 analysis selected Sylas/Jungle/16.21 and showed ten training matches, with item IDs 3152 in 9/10, 3020 in 7/10 and 3157 in 4/10 inventories.
- **Private feedback notebook:** self reflections and explicitly unverified peer reports, two 1–5 ratings, a maximum 500-character observation and explicit consent. Stored in a separate `backend/data/private_feedback.sqlite3` file, not the expiring cache, never public reputation or model features. List, add, delete and per-match export are implemented. New private/provider/live endpoints require a loopback client, loopback Host, approved local Origin and custom request header; cross-site requests are rejected. Consent, bounds, extra fields and SQL parameters are checked. No genuine peer study or identity verification has occurred.
- **Prospective low-elo pipeline:** enrollment captures a fresh solo rank and the frozen model hash; only later games within 30 days qualify. Iron/Bronze/Silver describe the enrolled player, not every lobby participant. Training games, the old viewed holdout, games preceding model creation/enrollment and wrong-model enrollments are excluded. Games are deduplicated. Evaluation requires 20 games, three enrolled players and both outcomes; no performance is fabricated below that gate.
- **Opt-in self dashboard:** official local Game Client API, fixed `https://127.0.0.1:2999`, own active player + clock + own scores only. No full player list, enemy tracking, memory reading, automation or live win-probability output. TLS validation uses Riot's official public root certificate; redirects and public hosts are not followed. Synthetic mode is prominently labeled. Own gold/farm/vision/KDA and optional review prompts are implemented; effectiveness is unvalidated.
- **English/Korean:** new panels, forms, errors, build-card labels and caveats translate with the existing persistent language button. External item names and technical provider schemas remain as supplied. Desktop 1280px and mobile 390px layouts were checked with no horizontal overflow. English was restored after checking Korean.

## Exact evidence and checks

The original fixed split remains 83 earlier / 21 later genuine games. `build_item_evidence.py` fits frequency candidates only on those 83 games. Five-match group threshold and top-three candidates are fixed; no holdout tuning or model replacement occurs. On the **already-viewed** 21-game holdout, 95/210 participant inventories had candidates (45.238% coverage), spread over all 21 games. Match-averaged candidate presence precision was 0.594029, versus 0.124376 for the global training-frequency baseline on the same covered rows. Average within each game first. The 210 player rows are not independent games. This is exploratory item-choice coverage, **not item efficacy, strategy validation, low-elo validation or coaching improvement**.

`validate_low_elo.py` currently returns `insufficient_prospective_data`: **0 eligible future games, 0 enrolled players, no metrics**. The existing old matches have no prospective rank enrollment; current Bronze context cannot relabel them.

**Full backend suite passed:** the user supplied normal Cursor-terminal `check.cmd` output: **154 passed, one warning, six subtests passed in 26.75s**. This includes the 27 routing/collector checks omitted from the restricted-session run. The warning is Starlette's nonblocking httpx/httpx2 deprecation notice; dependencies were not changed. The earlier restricted-session result remains separate: 127 backend tests and six subtests passed. **26 frontend tests**, TypeScript and production build also passed. Focused checks cover provider allowlists/schema/session/cache, untrusted compact data, feedback persistence/consent/deletion/local access, fixed local HTTPS/redirect rejection, item split reproduction and temporal cohort exclusions. Earlier temporary-folder permission failures were resolved by setting TEMP/TMP inside the workspace; one test-only lifespan fixture was corrected to use mocked transports. The historical 135-test result applies to the preceding version, not this increment. See [full-suite receipt](QA_FULL_BACKEND_2026-10-30.txt).

Real-browser checks verified the new panels, genuine Riot analysis and item/cohort reports, actual OP.GG discovery/call/build cards, synthetic live mode, consent-disabled note saving, Korean labels and responsive widths. Real active-game telemetry, certificate setup on this machine, verified peer submissions, enrollment calls and a prospective study remain unverified. The restricted shell could not resolve the official certificate host; it did not disable certificate verification or replace a certificate.

Preserved hashes:

- Active model SHA256: `9a64650a4dade3b14c0370c999df8573b36da524cd6a413dee9b492a6cee017e`.
- Private raw dataset SHA256: `be988d94be1853b30b35ca6e3f8aaf4305be9a275a353666829e099bfe62368c`.

## Run the new tools

Restart `start.cmd` after updating backend source, then refresh the app. Below the selected match: connect OP.GG, choose a tier and click **Load champion build evidence**. The provider is queried only on request. Unusual champion spellings can be edited. Advanced querying uses the actual displayed provider schema. No Riot key or player ID is forwarded.

Use **Private behavior and peer notes** for a concrete observation, select its source and check consent before saving. No notes are pre-created on behalf of real players. Notes are private to this computer; this is not a multi-user authenticated feedback service. Export any notes you need before deleting them.

For own live stats, in a normal Cursor terminal from GradProject:

```powershell
.\setup-live.cmd
```

Then start an actual League game **on the same computer**, click **Connect my game**, and stop when finished. Certificate setup downloads only Riot's public certificate from `https://static.developer.riotgames.com/docs/lol/riotgames.pem` over verified HTTPS; it does not add a machine-wide trust certificate or change Riot API TLS. Synthetic mode works without a game/certificate. The app description in Riot's portal still needs updating to describe this new use before wider release; no approval for this increment is asserted.

For a consenting Iron/Bronze/Silver player, prospectively enroll first:

```powershell
.\.venv\Scripts\python.exe backend\scripts\enroll_low_elo.py --riot-id 'Molybdite#KR1' --platform kr --consent
```

The example is **not enrollment already performed**. Repeat only for players who actually consent. After they play later games, collect those completed matches with the existing collector, then evaluate:

```powershell
.\.venv\Scripts\python.exe backend\scripts\collect_matches.py --riot-id 'Molybdite#KR1' --platform kr --count 20
.\.venv\Scripts\python.exe backend\scripts\validate_low_elo.py
```

Collect each enrolled account's later history with the same collector. No autonomous collection loop or future promise is configured. Do not train/tune on the future cohort and then call it independent evaluation. More than the minimum is needed for strong conclusions; repeated players and patches remain limitations.

Regenerate inventory evidence with:

```powershell
.\.venv\Scripts\python.exe backend\scripts\build_item_evidence.py
```

The private source data is intentionally absent from review packages, so this command requires the retained local dataset. Weights, raw games, old report and slide files were not changed.

## Still needed for the full requested scope

- Documented authorized data access from **FOW, GGQ and DEEPLOL**. Their current links are not data integrations. No relevant connector was available in plugin discovery. Do not describe a link collection as a completed provider feature merge.
- Representative data and a prospective/controlled study for **validated item or strategy benefit**. Frequency/outcome correlations and passing tests cannot prove this.
- Authenticated consenting participants, correction/retraction and an actual study for **verified peer feedback** or behavioral prediction. Riot match stats do not establish communication, toxicity, AFK intent or psychological traits.
- Actual prospective rank-enrolled games for **dedicated low-elo evaluation**, followed by class/sample checks and honest reporting. No lost historical result was recovered or substituted.
- An active League game, official certificate setup and policy/application review for **real-game self dashboard validation**. Full live coaching/overlay/audio and its benefit are not complete.

The preserved 0.2 report/PPT predate this increment. Do not claim these new features or counts were reviewed in those documents or already submitted to school.

Primary references: [official OP.GG MCP](https://github.com/opgginc/opgg-mcp), [Riot Game Client API and policies](https://developer.riotgames.com/docs/lol).
