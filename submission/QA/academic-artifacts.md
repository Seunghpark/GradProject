# Version 0.6 academic review artifacts

Latest review files are in `../final_v06_2026-10-30`:

- `LolAi_FinalReport_v06_Review.docx` (editable official-cover report).
- `LolAi_FinalReport_v06_Review.pdf` (46-page native Word export).
- `소프트웨어학과_박승현(2019310202).pptx` (18 editable slides).

## Report verification

The user exported the original 46-page draft PDF. Each page was rendered with
pypdfium2 at scale 2 and visually inspected. The draft/PDF were preserved. The
contents field was fully refreshed in Word to include section 8 on body page 29;
the conclusion starts on body page 33. A new review DOCX removes only the personal
reflection's editorial draft marker and instruction to edit before submission,
retaining its factual first-person text for the student's review. No signature,
score, adviser opinion or new personal experience was added.

The clean file was opened/saved in installed Word and exported locally to PDF.
The final PDF has 46 pages, with body pages 1-43 after cover/contents. All changed
pages (3, 13, 36-38 and 40-46) were visually inspected again; the remaining 34
pages were pixel-identical to already reviewed pages. No clipped tables,
overlapping objects, missing glyphs or broken field references were found.
All figures/drawings, six tables including the two official cover tables and
five native equations remain. Empty official scoring/signature cells remain
empty. The original 21-game experiment and additional 35-game audit are separate.

The bundled DOCX renderer was unavailable because soffice.exe was absent. Native
Word export plus PDFium page rendering provided the verified fallback; no
unverified reflow renderer was substituted. Page texts and render hashes are
recorded in `v06_render/final`.

PDF SHA-256: `2d54ce9ebeb898f07707d21bedff5fde18272da2fec20a5ee9bdf104588708dc`.
The supplied draft PDF hash remains
`e1015400e6c8d3b34d34be209cf6f8405c6e16b7d61ef2b71ca654edb587eea2`.

## Presentation verification

The latest authoring revision is
`../presentations/v06_2026-10-30_r4/소프트웨어학과_박승현(2019310202).pptx`.
SHA-256: `65102981113f7c97ca0694221f132cd09b0a6cb7949b14630557841c3c389a1f`.
All 18 slides were rendered. Three inherited label/value spacing defects were
repaired in earlier revisions. Revision 4 adds the user-stated college beneath
the name on the cover. That slide was inspected; slides 2-18 are pixel-identical
to the previously inspected revision. Research figures/numbers are unchanged.

Package, native table/chart, font, geometry and first-party import checks passed.
The Windows sandbox denied the final hard-link publication; exclusive copy of
the same validated bytes succeeded and hashes matched. The first-party finalizer
did not return through its hard-link path; the copy receipt records this limit.

## Human review remains

Student reflection/contribution wording, the actual portal title, accepted report
format, adviser review/online signature and school submission still require the
student. No school upload or cloud backup is claimed. No new neural weights,
historical tier labels, coaching efficacy or recovered old experiment is claimed.
