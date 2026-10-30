# English and Korean interface — 2026-10-30

English is the default. The header's **한국어** button switches the entire
application interface to Korean; **English** switches it back. The explicit
choice is saved under `lolai-language` in this browser's local storage. If storage
is blocked or has an unknown value, the app starts in English and switching
continues to work for the current page.

## Coverage and data handling

Navigation, forms and client validation, source banners/errors, match results,
role names, profiles, charts/disclosures, post-match insights, known backend
notices, model methodology/evaluation, rank/mastery labels, resource controls,
video metadata labels and footer are translated. Dates and formatted metadata
use the selected locale. Page title, description and document language also update.
No translation service or new dependency is used.

Language changes preserve the loaded analysis, selected match and input state.
YouTube queries continue using canonical English role names so a language change
does not alter the search query/cache key or discard its loaded results.

Actual player/champion names, external video titles/channels and brand/model
proper names remain in their source form. The API payload and exported research
JSON are unchanged. Unknown future/upstream free text is displayed as received;
add its exact message/template to the catalogs when introducing new API messages.
Translation does not alter model weights, scores, caches or credential handling.

## Verification

- Frontend: **21 tests passed**, including the previous 13 and eight language
  tests. TypeScript and Vite production build passed.
- Tests cover English default and persisted Korean, unavailable storage,
  interpolation/placeholder parity, unknown/prototype-like strings, catalog
  coverage, composed API warnings, numerical insight translation, English and
  Korean SSR, profile/model/review semantics, and canonical video search queries.
- Actual running app: English loaded with the 한국어 control. Korean translated
  the full demo dashboard, numerical insights and methodology/model comparison.
  A DOM check found no remaining long English application paragraphs in the
  checked Korean dashboard; proper names are retained intentionally.
- Korean survived a page refresh. Switching from selected Syndra match
  DEMO_0003 back to English retained the same selected match.
- Submitting an empty Riot ID showed Korean validation and retained the previous
  results. Switching language immediately changed that existing error to English.
  The form uses its own validation to avoid browser-language-dependent native
  messages. English also survived refresh; the page was left in English.
- At a 390px viewport, document client/scroll width both measured 375px (scrollbar
  excluded) and the language control remained inside the viewport. At 1280px,
  both widths were 1265px. Temporary viewport overrides were reset.
- Backend was unchanged. Its earlier 135-test/six-subtest pass remains historical
  evidence; it was not rerun for this frontend-only change. No new genuine Riot
  or YouTube requests, clean-machine installation or exhaustive accessibility/device
  testing were required or performed for this update.

Current production assets: `index-C6AU6skD.js`, `index-CBqgixe0.css`.
The earlier report/PPT/review packages remain preserved and predate this UI update.
