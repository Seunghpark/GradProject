import {useI18n} from './i18n'

export type RankEntry={queue:string;tier:string;division:string;league_points:number;wins:number;losses:number;win_rate:number|null}
type Observation={observed_at:string;entries:RankEntry[]}
export type RankHistoryData={status:string;recorded_checks?:number;first_observed_at?:string|null;current_observation?:Observation|null;previous_observation?:Observation|null;observations:Observation[];cached_lookup?:boolean;previous_season_status?:string}

export default function RankHistory({history,current}:{history?:RankHistoryData;current:RankEntry[]}){
 const {t,locale}=useI18n()
 const observations=Array.isArray(history?.observations)?history.observations:[],previous=history?.previous_observation
 const date=(value:string)=>{const parsed=new Date(value);return Number.isFinite(parsed.valueOf())?parsed.toLocaleString(locale,{dateStyle:'medium',timeStyle:'short'}):'—'}
 const rank=(entry?:RankEntry)=>entry?`${t(entry.tier)} ${entry.division} · ${entry.league_points.toLocaleString(locale)} LP`:t('No rank returned')
 return <section className="rank-history" aria-label={t('Official rank history')}><h4>{t('Current vs previous recorded rank')}</h4>
 <p className="muted">{t('These are official Riot rank observations saved by LolAi, not estimated skill tiers or the rank at the time of a match.')}</p>
 {previous?<><p>{t('Previous recorded check: {date}',{date:date(previous.observed_at)})}</p><dl className="metadata">{['RANKED_SOLO_5x5','RANKED_FLEX_SR'].map(queue=>{const old=previous.entries.find(entry=>entry.queue===queue),now=current.find(entry=>entry.queue===queue),sameDivision=old&&now&&old.tier===now.tier&&old.division===now.division,delta=old&&now?now.league_points-old.league_points:null;return <div key={queue}><dt>{t(queue==='RANKED_SOLO_5x5'?'Ranked solo/duo':'Ranked flex')}</dt><dd>{rank(old)} → {rank(now)}{sameDivision&&delta!==null&&<small>{t('Same-division LP change: {change}',{change:`${delta>0?'+':''}${delta.toLocaleString(locale)}`})}</small>}{old&&now&&!sameDivision&&<small>{t('Tier or division changed; LP is not combined across ranks.')}</small>}</dd></div>})}</dl></>:<p>{t(observations.length&&!history?.current_observation?'The current response has no matching saved observation. Previously recorded ranks are listed below.':'No previous recorded rank is available yet. Fresh rank lookups will build history from now on.')}</p>}
 {history?.status==='storage_unavailable'&&<p role="status">{t('Rank history could not be saved. Your current Riot rank is still shown.')}</p>}
 {history?.first_observed_at&&<p>{t('History starts: {date}',{date:date(history.first_observed_at)})} · {t('{count} recorded checks',{count:history.recorded_checks??0})}</p>}
 {observations.length>0&&<details><summary>{t('Recorded rank timeline (latest 20 checks)')}</summary><div className="profile-table-scroll" role="region" aria-label={t('Recorded ranks')} tabIndex={0}><table className="profile-table"><thead><tr><th>{t('Observed at')}</th><th>{t('Ranked solo/duo')}</th><th>{t('Ranked flex')}</th></tr></thead><tbody>{observations.map((row,index)=><tr key={`${row.observed_at}-${index}`}><th scope="row">{date(row.observed_at)}</th><td>{rank(row.entries.find(entry=>entry.queue==='RANKED_SOLO_5x5'))}</td><td>{rank(row.entries.find(entry=>entry.queue==='RANKED_FLEX_SR'))}</td></tr>)}</tbody></table></div></details>}
 <p className="muted">{t('Cached responses do not create new dated observations. This history is not an archive of earlier seasons.')}</p><p className="muted">{t('Previous season rank: not verified. No historical tier is filled in from current rank.')}</p>
 </section>
}
