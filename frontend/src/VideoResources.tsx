import {useEffect,useRef,useState} from 'react'
import {useI18n} from './i18n'

type Video={id:string;url:string;title:string;channel:string;published_at:string;views:number|null;patch_mentioned:boolean}
type Results={status:string;videos:Video[];notice:string;cached?:boolean;fetched_at?:string}
export function parseVideoResults(payload:unknown):Results|null{
 if(!payload||typeof payload!=='object')return null
 const result=payload as Partial<Results>
 if(!['ok','not_configured','unavailable'].includes(result.status??'')||typeof result.notice!=='string'||!Array.isArray(result.videos)||result.videos.length>6||(result.status!=='ok'&&result.videos.length>0))return null
 if(result.videos.some(video=>!video||typeof video.id!=='string'||!/^[-\w]{11}$/.test(video.id)||video.url!==`https://www.youtube.com/watch?v=${video.id}`||typeof video.title!=='string'||typeof video.channel!=='string'||typeof video.published_at!=='string'||!Number.isFinite(Date.parse(video.published_at))||typeof video.patch_mentioned!=='boolean'||(video.views!==null&&(typeof video.views!=='number'||!Number.isFinite(video.views)||video.views<0))))return null
 return result as Results
}
export default function VideoResources({champion,role,patch,valid}:{champion:string;role:string;patch:string;valid:boolean}){
 const {t,locale}=useI18n()
 const [order,setOrder]=useState('viewCount'),[days,setDays]=useState('30'),[result,setResult]=useState<{key:string;data:Results}|null>(null),[loading,setLoading]=useState(false),[error,setError]=useState('')
 const request=useRef<AbortController|null>(null)
 const key=JSON.stringify([champion,role,patch,order,days,valid]),data=result?.key===key?result.data:null
 useEffect(()=>{request.current?.abort();setResult(null);setError('');setLoading(false);return()=>request.current?.abort()},[key])
 async function load(){
  if(!valid)return
  request.current?.abort();const controller=new AbortController();request.current=controller;setLoading(true);setError('')
  try{const params=new URLSearchParams({champion,role,patch,order,days}),response=await fetch(`/api/videos?${params}`,{signal:controller.signal});if(!response.ok)throw new Error('Video search is unavailable. Check that the latest backend is running.');const payload=parseVideoResults(await response.json());if(!payload)throw new Error('The video service returned an unexpected response.');if(!controller.signal.aborted)setResult({key,data:payload})}catch(failure){if(!controller.signal.aborted)setError(failure instanceof Error?failure.message:'Video search failed.')}finally{if(!controller.signal.aborted)setLoading(false)}
 }
 return <div className="video-resources" aria-busy={loading}>
  <h4>{t('Recent videos')}</h4><p className="muted">{t('Load video titles, publication dates and view counts for this champion and patch.')}</p>
  <div className="resource-links"><label>{t('Sort videos')} <select aria-label={t('Sort videos')} value={order} onChange={event=>setOrder(event.target.value)}><option value="viewCount">{t('Most viewed')}</option><option value="date">{t('Newest')}</option></select></label><label>{t('Publication window')} <select aria-label={t('Video publication window')} value={days} onChange={event=>setDays(event.target.value)}><option value="14">{t('{days} days',{days:14})}</option><option value="30">{t('{days} days',{days:30})}</option><option value="90">{t('{days} days',{days:90})}</option></select></label><button type="button" className="secondary-button" onClick={()=>void load()} disabled={loading||!valid}>{t(loading?'Loading videos…':'Load video results')}</button></div>
  <p role="status" className="sr-only">{loading?t('Loading videos for the selected champion and patch.'):''}</p>
  {error&&<p role="alert">{t(error)}</p>}
  {data&&<div aria-live="polite"><p className="small muted">{t(data.notice)}{data.cached?` ${t('Cached results (up to 6 hours).')}`:''}</p>{data.status==='ok'&&!data.videos.length&&<p>{t('No videos were returned for this search. Try a wider publication window.')}</p>}<ul>{data.videos.map(video=><li key={video.id}><a href={video.url} target="_blank" rel="noopener noreferrer">{video.title}</a><p className="small muted">{video.channel} · {new Date(video.published_at).toLocaleDateString(locale)} · {video.views===null?t('View count unavailable'):t('{views} views',{views:video.views.toLocaleString(locale)})} · {t(patch?(video.patch_mentioned?'Patch mentioned in text':'Patch not found in text'):'No patch filter')}</p></li>)}</ul></div>}
 </div>
}
