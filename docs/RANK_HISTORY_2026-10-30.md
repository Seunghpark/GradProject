# Official rank history and optional season archives — backend 0.4.1

Priority confirmed by the user: make the native program and backend reliable first. Visual redesign and any statistical skill-tier estimate are deferred. No skill-tier estimator, MMR/ELO calculator or current-rank backfill into historical training labels was added.

## Implemented

`GET /api/player-context` remains the source of validated **current Riot ranks**. It now also returns `rank_history` with dated observations, the previous recorded check, the first observation date and the latest 20 checks. All observations remain stored; 20 is a display limit, not a deletion policy.

- Fresh, validated rank responses are recorded in `backend/data/rank_history.sqlite3`, alongside the configured API cache file. This database is independent of the expiring response cache.
- Repeated cached lookups do not receive new observation timestamps. Two genuinely fresh checks with the same rank remain two dated observations.
- Solo and flex remain separate. Missing ranks remain missing; no entry does not become a fake Iron tier.
- Current vs previous LP differences are shown only within the same tier and division. Different ranks are not converted into a new rating scale.
- Saved history remains readable during an upstream rank failure. Storage failure does not hide an otherwise valid current Riot response.
- Local account keys are one-way digests. PUUIDs, names and API keys are not stored in the rank-observation table or returned in its history fields. A public Riot ID is already present separately in the context response.

No rank before the first observation is invented. The current Riot lookup is not the rank at the time of any historical game and does not enter prediction inputs or the verified-tier benchmark path.

## OP.GG capability check: actual positive result

Sources: [OP.GG's official MCP repository](https://github.com/opgginc/opgg-mcp), fixed official endpoint `https://mcp-api.op.gg/mcp`. No OP.GG or DeepLoL website was scraped and no proprietary service code was copied.

The user ran the read-only probes in the normal Cursor terminal because the restricted agent terminal cannot make those connections. The live schema was fetched at `2026-10-30T06:54:58.940625+00:00`: **29 tools total, 17 with the `lol_` prefix**. The LoL tools were:

- `lol_get_champion_analysis`, `lol_get_champion_synergies`, `lol_get_lane_matchup_guide`
- `lol_get_pro_player_riot_id`, `lol_get_summoner_game_detail`, `lol_get_summoner_profile`
- `lol_list_aram_augments`, `lol_list_champion_details`, `lol_list_champion_leaderboard`, `lol_list_champions`
- `lol_list_discounted_skins`, `lol_list_items`, `lol_list_lane_meta_champions`, `lol_list_skin_stats_for_champion`
- `lol_list_summoner_matches`, `lol_esports_list_schedules`, `lol_esports_list_team_standings`

`lol_get_summoner_profile` explicitly offered `previous_seasons`, `previous_season_tiers`, per-queue `rank_info` and `high_rank_info`. The follow-up profile probe fetched at `2026-10-30T07:00:33.758286+00:00` returned populated data for **Molybdite#KR1, Korea**. It contained eight solo-queue archives and one flex archive, with provider season IDs 17, 19, 21, 23, 25, 27, 29 and 31.

Example actually returned: **Season ID 31, solo queue, Silver III, 38 LP**, provider record time `2026-01-08T01:49:49+09:00`. Its separately reported peak was also returned and is deliberately kept separate. The latest available flex record was Season ID 27, Bronze I, 73 LP. These are OP.GG-supplied archival records, not independently verified final-season results. Season IDs are not silently translated into calendar years or split labels. This account's response does not establish ten years of history for every player.

The capability result was reported to the user before the optional archive integration was implemented.

## Optional backend endpoint

`GET /api/providers/opgg/rank-history?game_name=...&tag_line=...&platform=kr`

Requires the existing local boundary: loopback client and Host, `X-Lolai-Local: 1`, and a permitted local Origin when supplied. Only Korea is currently supported for this archive route, matching the region actually probed. Other regions remain supported by the primary Riot integration.

The route requests only identity and historical-rank fields. The generic three-tool champion/item allowlist is unchanged: clients cannot use this feature to call arbitrary profile tools or choose extra fields. Riot keys and PUUIDs are never forwarded to OP.GG.

OP.GG's compact class/constructor response is parsed as **data** using a restricted AST walker, without `eval`, execution, imports or interpretation of provider instructions. JSON responses are also supported. Identity must match the requested Riot ID; queue, tier, division, LP and fetch timestamps are validated. Conflicting duplicate season/queue entries are omitted, missing records are not filled and reported peak ranks remain distinct.

Normalized responses explicitly carry `provider=OP.GG`, `source=opgg_archive`, the original `fetched_at`, provider record dates, `independently_validated=false`, and explanatory provenance. A validated provider archive is stored separately from native Riot observations. During an outage, a saved archive can be returned with `served_from=saved_archive`, `cached=true`, its original fetch time and an explicit warning. An outage without a saved archive returns an error; it never invents a season rank.

The optional route is implemented at the API level. Connecting an archive card or redesigning the website is deferred with the rest of frontend work. This source is supporting context; native match calculations and champion aggregates do not depend on it. It does not populate verified historical-tier benchmarks or the prospective low-elo study.

## Executed checks

- User's normal Cursor full suite: **208 passed, one warning, six subtests passed in 23.78s**. This includes all HTTP and collector checks. The warning is the existing Starlette/httpx deprecation notice, not a failed check.
- Restricted-session regression: **180 passed, six subtests passed in 13.76s**, excluding the 28 normal-terminal HTTP/collector cases.
- Existing frontend regression: **40 tests, TypeScript and production build passed**. This preserves functional rank-history display; it is not a redesign effort.
- Running backend health verified as **0.4.1** after user restart.
- Live Riot context returned **Bronze II, 73 LP** for Molybdite#KR1 and saved its first official observation at `2026-10-30T07:10:00.526627+00:00`. A cached second request retained the same timestamp and count of one.
- Live native champion API returned 104 genuine local matches, 279 groups, patches 16.20/16.21 and solo queue.
- Live genuine-player analysis returned ten matches, ten roster rows and exactly one highlighted player in every match, plus eligible jungle review tips backed by 103 separate local reference matches.
- The user executed the running archive API with its required loopback/origin headers. It returned `status=available`, `provider=OP.GG`, `served_from=provider`, `storage_status=saved`, fetched at `2026-10-30T07:11:52.648268+00:00`, with Season ID 31 / Silver III / 38 LP. This live response matches the earlier MCP capability probe. Its mocked HTTP/cache/outage/security checks also pass.

The original raw match dataset and active MLP are preserved. Their hashes remain the same as the previous native-platform receipt. The lost XGBoost experiment, broad tier benchmarks, coaching efficacy, complete OP.GG feature parity and official school submission remain unclaimed.
