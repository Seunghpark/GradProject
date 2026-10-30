import {useI18n} from './i18n'
import type {TipsReport} from './types'

const LABELS:Record<string,string>={cs_per_min:'CS / min',early_cs:'Early CS (9–10 min)',gold_diff_10:'Role gold difference (9–10 min)',gold_diff_15:'Role gold difference (14–15 min)',kill_participation:'Kill participation (%)',damage_share:'Team damage share (%)',vision_per_min:'Vision/min',wards_placed_per_min:'Wards placed/min',wards_cleared_per_min:'Wards cleared/min',deaths_before_14:'Deaths before minute 14',objective_participation:'Recorded objective participation (%)'}
const ACTIONS:Record<string,string>={
 cs_per_min:'Review missed waves or idle camp time. Pick one repeatable farming habit for the next match.',
 early_cs:'Review the opening route, first recall and missed farm in the early replay.',
 gold_diff_10:'Review the opening trades, first recall and missed waves or camps against your role opponent.',
 gold_diff_15:'Review the transition after the first recall, farm access and risky trades against your role opponent.',
 kill_participation:'Review when you could safely join a nearby fight and when farming was more valuable.',
 damage_share:'Review fight access and target selection. Do not chase extra damage at the expense of a safe play.',
 vision_per_min:'Review ward timing and coverage near the next objective. A larger score alone is not better vision.',
 wards_placed_per_min:'Review whether wards covered useful routes before objectives; avoid placing wards just to raise a count.',
 wards_cleared_per_min:'Review safe opportunities to deny vision with teammates before objectives.',
 deaths_before_14:'Review the minute before each early death: information, escape route and the decision to commit.',
 objective_participation:'Review the recorded major-monster events and your route beforehand. Missing assists can undercount involvement.'
}
export default function ExplainableTips({report}:{report?:TipsReport}){
 const {t}=useI18n()
 return <section className="native-tips" aria-label={t('LolAi explainable tips')}><div className="panel-header"><div><h3>{t('Your largest consistent gaps')}</h3><p>{t('Our formula: gap × equal weight × recent consistency. Review priorities, not proven causes of losing.')}</p></div><span className="badge neutral">{t('Own algorithm')}</span></div>
 {!report||report.status!=='available'?<p className="muted">{t('Tips need at least three recent games in the same role, patch and queue, plus 30 separate reference matches per metric. Synthetic examples never use real-player benchmarks.')}</p>:<>
 <p className="native-tip-cohort">{t('Local {role} sample · patch {patch} · {games} recent games · {references} separate reference matches',{role:t(({TOP:'Top',JUNGLE:'Jungle',MIDDLE:'Mid',BOTTOM:'Bot',UTILITY:'Support'} as Record<string,string>)[report.role]??report.role),patch:report.patch??'—',games:report.recent_games??0,references:report.cohort_matches??0})}{report.champion?` · ${report.champion}`:''}</p><p className="muted">{t('Each displayed metric also needs ten distinct reference players. Repeated players can still limit independence; these are descriptive priorities, not statistical certainty.')}</p>
 <div className="native-tip-grid">{report.tips.map((tip,index)=><article key={tip.metric}><span className="section-caption">{t('Review priority {number}',{number:index+1})}</span><h4>{t(LABELS[tip.metric]??tip.metric)}</h4><p>{t('Your recent average: {actual}; local midpoint: {benchmark}. Performance percentile: {percentile}.',{actual:tip.actual.toFixed(2),benchmark:tip.benchmark.toFixed(2),percentile:tip.percentile.toFixed(0)})}</p><p className="muted">{t('Weaker than the local midpoint in {below} of {games} games; reference covers {matches} separate matches.',{below:tip.below_games,games:tip.recent_games,matches:tip.reference_matches})}</p><p>{t(ACTIONS[tip.metric]??'Review this match')}</p><details><summary>{t('Why this tip?')}</summary><p>{t('Gap {gap}% × equal weight {weight}% × weighted consistency {consistency}% = priority {priority}.',{gap:(tip.gap*100).toFixed(1),weight:(tip.impact_weight*100).toFixed(1),consistency:(tip.consistency*100).toFixed(1),priority:tip.priority.toFixed(4)})}</p></details></article>)}</div>
 {!report.tips.length&&<p>{t('No consistent below-midpoint gap met the display rules. No weakness is invented.')}</p>}
 {report.strength&&<p className="native-strength"><strong>{t('Relative strength')}: {t(LABELS[report.strength.metric]??report.strength.metric)}</strong> · {t('Performance percentile {percentile} in this local reference.',{percentile:report.strength.percentile.toFixed(0)})}</p>}
 </>}
 <details className="native-tip-method"><summary>{t('Benchmark and formula details')}</summary><p>{t('Compare the same role, patch and queue. Exclude your own reference rows and every loaded match. Use champion-specific references only when all reviewed games use that champion and at least 50 separate reference matches exist.')}</p><p>{t('Percentiles use tie midranks; lower early deaths is better. Gap is the shortfall below the 50th performance percentile. Consistency weights each older game by 0.85. Equal weights sum to one across usable metrics; they are not learned win-impact weights.')}</p><p>{t('Tier-comparison mode is implemented but unavailable here until verified pre-match rank data exists. No Gold or other tier is guessed. The lost XGBoost experiment has not been recovered.')}</p></details>
 </section>
}
