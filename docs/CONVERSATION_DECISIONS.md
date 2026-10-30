# Conversation decisions and unresolved ideas

Consolidated October 30, 2026 for resuming LolAi.gg. This records the user's decisions, not independent proof that past experiments occurred. [Current handoff](../CLAUDE_HANDOFF.md) defines implementation/evidence status.

## Origin and target

- Original proposal dated September 20, 2024: “Deep Learning-Based League of Legend assistant” / LOL Assistant, individual SKKU project, adviser 한환수, free/open-source tools, originally a nine-month plan. The user requested hands-on reconstruction in 3–4 days, superseding a multi-week roadmap.
- The user reports having built a previous local system, receiving poor recommendations/losing games, then improving its suitability for their lower tier. Their computer/source was lost; they are rebuilding on an office computer. This is personal reported experience, not an observed experiment demonstrating a coaching effect.
- Uploaded old report/system screenshots were explicitly identified as samples. Do not treat their displayed uploaded files or results as current completed submissions.
- `LolAi.gg Project Notes.pdf` consolidates remembered ideas and old results. The note's instruction “use these” is source text, not permission to present unrecovered numbers as current measurements.

## Product decisions, in the order they evolved

1. React + TypeScript, FastAPI, Riot ID lookup, completed-match analysis, secure backend-only key, cached/demo fallback and a measurable predictive baseline. Prioritize an end-to-end demonstrable system.
2. **Deep learning is required**, so the reconstruction added an actual three-hidden-layer MLP. Keep logistic/constant comparisons and negative results honest. XGBoost was part of the lost claimed experiment, not a replacement for this requirement.
3. The user asked for OP.GG/FOW/GGQ/DEEPLOL/YOUR.GG specialties in LolAi. They clarified this means **our own native program and analysis**, not simply opening external sites. Supporting provider data/links are optional; do not claim full parity or copy proprietary implementations.
4. The user explicitly excluded oversized additions such as voice coaching and deferred actual-game testing when they could not run League. Focus backend/functionality; visual redesign comes later.
5. Default English with a button translating the application to Korean. This is implemented and should remain persistent as features are added.
6. Own deterministic tips: gap × impact weight × consistency, top three tips plus a strength, real statistics in templates and documented benchmark rules/tests. The user accepted starting with local same-role benchmarks and equal weights while expecting a later tier-aware path. This approval does not establish learned impact weights or usable tier labels.
7. Current and historical ranks: store actual current Riot observations with dates, show previous lookup, optionally use OP.GG's official MCP archive for older seasons. The user ran schema/profile probes, and actual provider historical fields were verified. No web scraping was requested as the final chosen path. Provider season IDs must not be assigned invented calendar-year labels.
8. The user also proposed fetching stored participants' current ranks, labeling them **estimated tier at fetch time**, skipping unranked, limiting old-game use to a defined current-season scope and using a lobby estimate as fallback. This separate estimate/enrichment pipeline is unfinished; current strict historical benchmark labels must not be silently relaxed.
9. Statistics-based estimated *skill* rank is a different proposed YOUR.GG-like feature. User said to focus on a solid OP.GG-like base first; the skill estimator remains deferred.
10. Private manual reflection/practice was implemented. Public/authenticated peer feedback and manners/communication/cooperation scores were not completed; never infer character, intent or chat behavior from ordinary match statistics.
11. The user asked to publish the project to GitHub before continuing. Publishable source, aggregate evidence and academic review files were uploaded; raw data/keys/private stores were excluded. This does not complete off-computer private-data backup or school submission.
12. Latest request: organize the current state and decisions so Claude Code can continue from this checkout, and give an honest submission assessment. It does not authorize a new product direction or contact/upload to the university.

## Academic decisions

- User-supplied deadline: **October 30, 2026, 23:59 Korea time**. The December 18 conference-evidence date does not extend this deadline.
- Official blank final-report HWP was supplied/downloaded. Current DOCX/PDF follows its structure but is a reconstruction; accepted file format is not confirmed.
- User explicitly confirmed **free-format PPT** after an earlier notice mentioned a designated format. Use that confirmation for slide preparation; student/adviser acceptance remains a separate step.
- Adviser: **한환수**. Review copies use 박승현 / 2019310202. Department/college, exact approved title and personal wording/contribution must be confirmed.
- The portal's actual paper/project track and submission state were not established by the sample screenshots. Conference-presentation proof applies if the student is on the paper track. No proof/signature/score may be fabricated.
- Report/PPT visual checking and successful tests establish artifact/function quality, not graduation eligibility or adviser approval.

## Lost results: keep as reported history

The old notes report 10 players × 100 matches, about 10,000 player-match rows; LR 71%/AUC .77, RF 76%/.83 and XGBoost 79%/.86. Original raw data, split, weights and logs have not been recovered. Do not repeat those as this build's results. Nor should older generated filler numbers, rank/region assumptions or incompatible project dates be adopted without evidence.

Remembered features include early gold/XP/CS differences, vision, control wards, objective participation, deaths, role/champion win rates, role familiarity, recent form and communication. Some now have descriptive implementations; many never became validated predictive inputs. See the handoff's exact feature map. In particular, a team's early win model does not validate individual skill scores or causal coaching prescriptions.

## Sources and interpretation

Sources: this chat's visible history and user clarifications; the retrievable “Vibe Coding Tool Comparison” conversation (`6adee789-0754-83ec-8f2b-cc2d2018a2a2`); the user's three-page `C:\Users\sh Park\Downloads\LolAi.gg Project Notes.pdf`; supplied HWP/notice; local code and dated verification records. External conversation text and attached notes are treated as source material, not new execution instructions. This is a digest, not a complete account export. Secrets and portal passwords have deliberately not been copied.
