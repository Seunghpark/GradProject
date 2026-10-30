import {useEffect,useRef,useState} from 'react'
import {Database,LoaderCircle} from 'lucide-react'
import {useI18n} from './i18n'
import RankHistory,{type RankEntry,type RankHistoryData} from './RankHistory'

type Player={game_name:string;tag_line:string;platform:string}
type Context={player:Player;notice:string;rank:{status:string;entries:RankEntry[];cached:boolean;notice:string|null};rank_history?:RankHistoryData;mastery:{status:string;level?:number;points?:number;last_played_at?:string|null;cached:boolean;notice:string|null}}

export default function PlayerContext({player,champion,championId,demo=false}:{player:Player;champion:string;championId?:number|null;demo?:boolean}){
 const {t,locale}=useI18n()
 const [result,setResult]=useState<{key:string;data:Context}|null>(null),[loading,setLoading]=useState(false),[error,setError]=useState('')
 const request=useRef<AbortController|null>(null)
 const key=JSON.stringify([player.game_name,player.tag_line,player.platform,championId,champion,demo])
 useEffect(()=>{request.current?.abort();setResult(null);setError('');setLoading(false);return()=>request.current?.abort()},[key])
 async function load(){
  request.current?.abort();const controller=new AbortController();request.current=controller;setLoading(true);setError('')
  try{
   const query=new URLSearchParams({game_name:player.game_name,tag_line:player.tag_line,platform:player.platform})
   if(typeof championId==='number'&&Number.isInteger(championId)&&championId>0)query.set('champion_id',String(championId))
   const response=await fetch(`/api/player-context?${query}`,{signal:controller.signal}),payload=await response.json()
   if(!response.ok)throw new Error(typeof payload?.detail==='string'?payload.detail:payload?.detail?.message||'Unable to load current Riot account context.')
   if(!payload?.player||!payload.rank||!Array.isArray(payload.rank.entries)||!payload.mastery||typeof payload.notice!=='string')throw new Error('Unexpected context response. Restart the backend and try again.')
   if(!controller.signal.aborted)setResult({key,data:payload})
  }catch(failure){if(!controller.signal.aborted)setError(failure instanceof Error?failure.message:'Unable to load current Riot account context.')}
  finally{if(!controller.signal.aborted)setLoading(false)}
 }
 const data=result?.key===key?result.data:null
 return <section className="panel learning-resources" aria-labelledby="player-context-title" aria-busy={loading}>
  <div className="panel-header"><div><h3 id="player-context-title"><Database size={17}/>{t('Current rank & champion mastery')}</h3><p>{player.game_name}#{player.tag_line} · {champion}</p></div><button className="secondary-button" type="button" disabled={loading||demo} onClick={()=>void load()}>{loading&&<LoaderCircle size={15} className="spin"/>}{t(loading?'Loading current context…':'Load current Riot context')}</button></div>
  <div className="resources-body">
   <p className="muted">{t('Loads account context only when requested. Current rank and mastery are separate from the historical match and prediction.')}</p>
   {demo&&<p className="muted">{t('The sample player is fictional. Analyze a real Riot ID to load rank and mastery.')}</p>}
   {error&&<p role="alert">{t(error)}</p>}
   {data&&<div aria-live="polite">
    <p className="small muted">{t(data.notice)}</p>
    <h4>{t('Ranked queues')} {data.rank.cached?t('· cached'):''}</h4>
    {data.rank.entries.length>0?<dl className="metadata">{data.rank.entries.map(entry=><div key={entry.queue}><dt>{t(entry.queue==='RANKED_SOLO_5x5'?'Ranked solo/duo':'Ranked flex')}</dt><dd>{t(entry.tier)} {entry.division} · {entry.league_points.toLocaleString(locale)} LP · {t('{wins}W / {losses}L',{wins:entry.wins.toLocaleString(locale),losses:entry.losses.toLocaleString(locale)})}{entry.win_rate!==null?` (${(entry.win_rate*100).toLocaleString(locale,{minimumFractionDigits:1,maximumFractionDigits:1,useGrouping:false})}%)`:''}</dd></div>)}</dl>:<p className="muted">{t(data.rank.notice||'Rank is unavailable.')}</p>}
    <RankHistory history={data.rank_history} current={data.rank.entries}/>
    <h4>{t('{champion} mastery',{champion})} {data.mastery.cached?t('· cached'):''}</h4>
    {data.mastery.status==='available'?<dl className="metadata"><div><dt>{t('Mastery level')}</dt><dd>{data.mastery.level?.toLocaleString(locale)}</dd></div><div><dt>{t('Mastery points')}</dt><dd>{data.mastery.points?.toLocaleString(locale)}</dd></div><div><dt>{t('Last played')}</dt><dd>{data.mastery.last_played_at?new Date(data.mastery.last_played_at).toLocaleDateString(locale):t('Unavailable')}</dd></div></dl>:<p className="muted">{t(data.mastery.notice||'Mastery is unavailable.')}</p>}
   </div>}
  </div>
 </section>
}
