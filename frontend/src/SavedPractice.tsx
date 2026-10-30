import {useState} from 'react'
import type {Analysis} from './types'
import {GOAL_LABELS,type GoalMetric} from './native'
import {useI18n} from './i18n'
import {localRequest} from './ResearchTools'

type Target={id:string;role:string;metric:string;target:number;patch:string;baseline_games:number;baseline_average:number;status:string;future_games:{id:string;actual:number;met:boolean}[];followup_average:number|null;observed_change:number|null}
export default function SavedPractice({player,role,metric,target,enabled}:{player:Analysis['player'];role:string;metric:GoalMetric;target:number;enabled:boolean}){
 const {t,roleName}=useI18n(),[targets,setTargets]=useState<Target[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false),[pending,setPending]=useState<string|null>(null)
 const query=new URLSearchParams({game_name:player.game_name,tag_line:player.tag_line,platform:player.platform})
 async function load(){setBusy(true);setError('');try{const result=await localRequest(`/api/practice?${query}`);setTargets(result.targets)}catch(failure){setError((failure as Error).message)}finally{setBusy(false)}}
 async function save(){setBusy(true);setError('');try{await localRequest(`/api/practice?${query}`,{method:'POST',body:JSON.stringify({role,metric,target})});const result=await localRequest(`/api/practice?${query}`);setTargets(result.targets)}catch(failure){setError((failure as Error).message)}finally{setBusy(false)}}
 async function remove(id:string){setBusy(true);setError('');try{await localRequest(`/api/practice/${id}?${query}`,{method:'DELETE'});setTargets(old=>old.filter(row=>row.id!==id));setPending(null)}catch(failure){setError((failure as Error).message)}finally{setBusy(false)}}
 return <details><summary>{t('Track practice across sessions')}</summary><p>{t('Save a private target with a frozen baseline from at least three collected games. Compare only the first three later games in the same role, patch and queue.')}</p>
 <button className="secondary-button" onClick={save} disabled={!enabled||busy}>{t('Save this target in LolAi')}</button>{' '}<button className="secondary-button" onClick={load} disabled={busy||!enabled}>{t('Load stored targets')}</button>
 {error&&<p role="alert">{t(error)}</p>}{targets.map(row=><article key={row.id}><strong>{roleName(row.role)} · {t(GOAL_LABELS[row.metric]??row.metric)} · {row.target}</strong><p>{t('Baseline: {average} across {games} games; patch {patch}.',{average:row.baseline_average.toFixed(2),games:row.baseline_games,patch:row.patch})}</p><p>{t('{count} of 3 later games loaded.',{count:row.future_games.length})}</p>{row.followup_average!==null&&<p>{t('Follow-up average: {average}; observed change: {change}.',{average:row.followup_average.toFixed(2),change:(row.observed_change??0).toFixed(2)})}</p>}{pending===row.id?<><button onClick={()=>void remove(row.id)} disabled={busy}>{t('Confirm deletion')}</button><button onClick={()=>setPending(null)}>{t('Cancel')}</button></>:<button className="secondary-button" onClick={()=>setPending(row.id)} disabled={busy}>{t('Delete stored target')}</button>}</article>)}
 <p className="muted">{t('Targets are private local records, not verified experiments. An observed change does not prove that advice caused improvement.')}</p></details>
}
