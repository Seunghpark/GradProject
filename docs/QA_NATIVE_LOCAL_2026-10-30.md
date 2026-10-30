# Native 0.4.0 verification — partial runtime check

Date: 2026-10-30, Asia/Seoul.

## Executed checks

- Restricted-session backend command: `.venv/Scripts/python.exe -m pytest -q --ignore=backend/tests/test_api.py --ignore=backend/tests/test_collect.py --basetemp=.tmp/pytest-native-final` with workspace TEMP/TMP. Result: **153 passed, six subtests passed in 14.46s**. The omitted 27 normal-terminal API/collector checks are not included in this number.
- Frontend: `tsc -b`, `node --test --test-isolation=none tests/*.test.mjs`, `vite build`. Result: **38 tests passed**, TypeScript and production build passed. Final assets: `index-RiL0xLEZ.css` and `index-DLQUoPAr.js`.
- Local catalog build: **104 genuine matches, 279 champion/role/patch/queue groups**.
- Local tip-benchmark build: **104 genuine matches, 1,040 participant rows, zero verified tier labels**.
- Genuine-record offline analysis: 20 selected-player matches; ten scoreboard rows; available local tip supported by **83 separate reference matches** after excluding player/loaded matches; tier status remains `requires_verified_rank_data`.

## Browser observations before restart

The browser loaded the new interface from the running server, including the Champions & builds navigation, personal form/goal tools and optional closed references section. English and Korean labels render. At the actual 467px browser viewport, document width is also 467px (no page-wide horizontal overflow in the observed dashboard).

On the fictional DemoPlayer account, a vision/min target was saved. Current games were correctly excluded (`0 of 3 later games loaded`); the target survived refresh and was then cleared through the app. No real player's goal was altered.

The external learning-resource and experimental live components were absent while the optional section was closed, mounted when explicitly opened and unmounted when closed. The live stop control was disabled: no game connection or polling was started. The app was left in English with optional tools closed.

**The running backend still displayed the old-version notice.** Fresh 0.4.0 HTTP/native-scoreboard/champion/tip interactions have not been verified in that process. The prepared code and build need a user restart via `start.cmd`; the restricted session cannot replace the normal Windows server. Do not treat the older backend's 154-test full-suite receipt as a pass for this increment.

## Preserved artifacts

Raw dataset SHA-256: `be988d94be1853b30b35ca6e3f8aaf4305be9a275a353666829e099bfe62368c`.

Active MLP SHA-256: `9a64650a4dade3b14c0370c999df8573b36da524cd6a413dee9b492a6cee017e`.

Separate source/build/derived-data review backup: `submission/LolAi_Native_Platform_2026-10-30.zip`, **151 files, 1,519,265 bytes**, SHA-256 `15d8e927c7fae1f7fde395edeb2b6b8d555aded3a61356f6c0e556fb52c4977a`. ZIP CRC, per-file hashes and credential-shaped-value exclusion passed. Raw matches, keys, private notes, caches and dependencies are excluded. This receipt was written after that snapshot; it is a companion record.

Existing report/PPT review files and previous archives were preserved. No school upload, adviser approval, Git push, public hosting, actual-game test or coaching-efficacy claim occurred.
