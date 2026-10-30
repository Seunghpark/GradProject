# Automatic collection and paged history — backend 0.5.0

## What changed

Successful genuine Riot lookups now feed LolAi's own persistent match collection.
Each eligible match is saved once by match ID. A later, more complete timeline
can upgrade that record without adding another match. Synthetic demo records
are excluded. Champion, final-inventory and matchup aggregates, plus the local
tip-reference cohort, refresh together from the collection.

The original `backend/data/riot_matches.jsonl` is imported at startup, without
rewriting it. Newly fetched matches go to `backend/data/match_store.sqlite3`.
Both native-statistics snapshots are published in a single SQLite transaction.
Failed imports roll back the attempted batch; failed refreshes preserve the
previous complete snapshots and the successfully collected raw records.

This is data collection, not model training. The active MLP, temporal models,
fixed research split, evaluation and original JSONL are unchanged. More stored
matches do not constitute a new model result or verified tier cohort. Current
rank observations and OP.GG archives remain separate from historical labels.

## API use

The existing interface continues to work. New paging and standalone detail are
backend API capabilities; a website history control is deferred with other
interface work.

From a normal Cursor PowerShell terminal while the server runs:

```powershell
$page = Invoke-RestMethod 'http://127.0.0.1:8000/api/analysis?game_name=Molybdite&tag_line=KR1&platform=kr&mode=live&count=10&start=0'
$page | Select-Object source, ingestion, dataset, pagination | ConvertTo-Json -Depth 6
```

`count` remains 1–20 per API request. `start` is 0–10000, an application safety
bound. Follow `pagination.next_start` until it is null. The offset counts raw
history IDs, including duplicate, unavailable and ineligible entries, rather
than the number of displayed games. After an interrupted page it points to the
first unprocessed ID, so that retrying does not skip that position. A full page
can provisionally advertise another page even when the next page is empty.
Offsets refer to Riot's current history order: a newly completed game can shift
positions between requests. Saved match IDs still deduplicate those overlaps.

```powershell
$offset = $page.pagination.next_start
if ($null -ne $offset) {
    $next = Invoke-RestMethod "http://127.0.0.1:8000/api/analysis?game_name=Molybdite&tag_line=KR1&platform=kr&mode=live&count=10&start=$offset"
}
$matchId = $page.matches[0].id
$detail = Invoke-RestMethod "http://127.0.0.1:8000/api/matches/${matchId}?game_name=Molybdite&tag_line=KR1&platform=kr"
Invoke-RestMethod 'http://127.0.0.1:8000/api/dataset/status'
```

The detail route verifies that the selected player participated and that the
match ID belongs to the requested routing region. It returns one match with
the existing native scoreboard and analysis. Saved complete records are reused;
partial timelines can be retried through the existing rate-limited Riot client.
Riot authentication remains backend-only.

Responses report ingestion counts and data revisions. Repeating a cached
analysis reports zero new writes instead of repeating its original `added`
count. Analysis cache keys include both collection and aggregate revisions.
If persistence or refresh fails, usable analysis remains available with a
warning, and the failed save is not cached as a success. `/api/dataset/status`
reports `aggregates_current` without exposing raw player records or file paths.

The command-line research collector also supports `--start` and `--pages`:

```powershell
.venv\Scripts\python.exe backend\scripts\collect_matches.py --riot-id 'Molybdite#KR1' --platform kr --count 100 --start 0 --pages 2 --output backend/data/extended_collection.jsonl
```

Collector `count` is 1–100 and `pages` 1–20; final page offset must remain within
10000. It stops at short or empty pages, deduplicates saved IDs and preserves
completed writes on a later Riot failure. Its explicit JSONL output is separate
from automatic API ingestion. Use a new output file to preserve the fixed
research snapshot; training or enrolling a new evaluation cohort is a separate
operation.

## Storage and recovery

Default server configuration imports the existing source and enables the local
SQLite store. Optional `MATCH_STORE_PATH` and `MATCH_SEED_PATH` values are
documented in `.env.example`; a blank store path disables automatic collection.
Isolated tests disable persistence unless they explicitly configure a store.

SQLite and raw player records remain ignored by Git and excluded from review
ZIPs. Keep a separate private backup of these files if collected matches must
survive loss of this computer. Stop the server before ordinary file copying,
or use SQLite's backup facility while it is running. A source ZIP is not a data
backup. No off-computer backup has been verified.

Native aggregates currently rebuild over the whole local collection when it
changes. This is suitable for the small local demonstration; incremental
aggregation and load tests are needed before scaling to many thousands of
matches. Same-length upstream corrections are not automatically substituted
for an already saved timeline. No scheduled crawler runs in the background.

## Checks and evidence

- Restricted-session regression: **223 passed, two deselected, six subtests
  passed in 16.04s**. The separate API test module was excluded; its 27 tests
  and two original asyncio collector tests require the normal terminal.
- User-confirmed normal Cursor-terminal full suite: **252 passed, one warning,
  six subtests passed in 28.05s**. [Receipt](QA_FULL_BACKEND_0_5_0_2026-10-30.txt).
  The warning is the existing Starlette/httpx deprecation notice. The earlier
  208-test receipt remains historical evidence for 0.4.1.
- Frontend: **40 tests**, TypeScript and production build passed. Only the
  storage-failure notice translation changed; no design changes were made.
- Offline genuine import: **104 unique matches**, **279 champion groups**,
  **1040 benchmark rows**, collection and aggregate revision **1**, current.
  Initialization completed in approximately **7.27 seconds** on this computer.
- Added checks cover persistence, duplicates, timeline upgrades, synthetic
  exclusion, corrupt-seed rollback, transactional snapshot failures, concurrent
  repeated ingestion, paging bounds/cache isolation, interrupted-page resume,
  standalone detail/player validation, failed-save handling and demo isolation.
- Original JSONL SHA-256:
  `be988d94be1853b30b35ca6e3f8aaf4305be9a275a353666829e099bfe62368c`.
  Active model SHA-256:
  `9a64650a4dade3b14c0370c999df8573b36da524cd6a413dee9b492a6cee017e`.

## Live acceptance after restart

The browser confirmed health version **0.5.0**, with the imported 104-match store
at revision 1. For Molybdite#KR1 in Korea, a two-ID page at offset 0 saved two new
matches: **106 total**, revision 2, `aggregates_current=true`, next offset 2.
Repeating it returned `source=cache`, `status=cached_analysis` and all write
counts zero, with the collection still at 106.

The next two-ID page at offset 2 returned different matches and saved two more:
**108 total**, revision 3, current. Both returned ten players and exactly one
selected player. The native champion catalog also reported **108 matches,
283 groups**, collection/aggregate revision 3. Standalone detail for
`KR_8437659775` reused saved data, returned ten players and one selected player,
and reported one duplicate and zero additions. A subsequent synthetic demo page
reported `synthetic_not_collected`; the dataset remained **108**, revision 3.

Compact browser evidence is saved locally in `.tmp/collection-0-5-live.json`;
it omits the player's PUUID and raw records. The API test is a successful path
check, not a representative network-failure, quota, load or clean-install test.
The SQLite collection grows; the fixed research JSONL remains 104 games. Its
hash and the active model hash were checked again after the live requests.
No model training, recommendation efficacy result, school upload or report/PPT
revision is implied. The lost original experiment remains unrecovered.
