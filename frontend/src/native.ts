import type {Match} from './types'

export const GOAL_METRICS=['cs_per_min','vision_per_min','kill_participation','deaths'] as const
export type GoalMetric=typeof GOAL_METRICS[number]
export const GOAL_LABELS:Record<string,string>={cs_per_min:'CS / min',vision_per_min:'Vision/min',kill_participation:'Kill participation (%)',deaths:'Deaths per game'}
export type PracticeGoal={version:1;role:string;metric:GoalMetric;target:number;created_at:number;excluded_ids:string[]}
export function playedAt(value:Match['played_at']):number{return typeof value==='number'?(value<1e12?value*1000:value):Date.parse(value)}
export function formSummary(matches:Match[]){
 if(!matches.length)return null
 return {games:matches.length,wins:matches.filter(match=>match.win).length,
  cs_per_min:matches.reduce((sum,match)=>sum+match.cs_per_min,0)/matches.length,
  vision_per_min:matches.reduce((sum,match)=>sum+match.vision_score/match.duration_minutes,0)/matches.length,
  deaths:matches.reduce((sum,match)=>sum+match.deaths,0)/matches.length,
  kill_participation:matches.reduce((sum,match)=>sum+match.kill_participation,0)/matches.length}
}
export function recentForm(matches:Match[],role:string){
 const sorted=matches.filter(match=>match.role===role&&Number.isFinite(playedAt(match.played_at))).sort((a,b)=>playedAt(b.played_at)-playedAt(a.played_at)||a.id.localeCompare(b.id))
 return sorted.length>=10?{recent:formSummary(sorted.slice(0,5))!,previous:formSummary(sorted.slice(5,10))!}:null
}
export function parseGoal(value:unknown):PracticeGoal|null{
 if(!value||typeof value!=='object')return null
 const goal=value as PracticeGoal
 const max=goal.metric==='kill_participation'?100:goal.metric==='vision_per_min'?10:30
 return goal.version===1&&['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'].includes(goal.role)&&GOAL_METRICS.includes(goal.metric)
  &&typeof goal.target==='number'&&Number.isFinite(goal.target)&&goal.target>=0&&goal.target<=max
  &&typeof goal.created_at==='number'&&Number.isFinite(goal.created_at)&&goal.created_at>0
  &&Array.isArray(goal.excluded_ids)&&goal.excluded_ids.length<=100&&goal.excluded_ids.every(id=>typeof id==='string'&&id.length<=40)?goal:null
}
export function goalProgress(goal:PracticeGoal,matches:Match[]){
 const seen=new Set<string>()
 return matches.filter(match=>{if(seen.has(match.id))return false;seen.add(match.id);return match.role===goal.role&&!goal.excluded_ids.includes(match.id)&&playedAt(match.played_at)>goal.created_at})
  .sort((a,b)=>playedAt(a.played_at)-playedAt(b.played_at)||a.id.localeCompare(b.id)).slice(0,3).map(match=>{
   const actual=goal.metric==='vision_per_min'?match.vision_score/match.duration_minutes:goal.metric==='kill_participation'?match.kill_participation*100:match[goal.metric]
   return {id:match.id,actual,met:goal.metric==='deaths'?actual<=goal.target:actual>=goal.target}
  })
}
export const elapsed=(milliseconds:number)=>`${Math.floor(milliseconds/60000)}:${String(Math.floor(milliseconds/1000)%60).padStart(2,'0')}`
