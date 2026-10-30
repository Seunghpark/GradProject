import {useEffect,useState} from 'react'
import {BookOpen,ArrowUpRight} from 'lucide-react'
import type {Match} from './types'
import {normalizePatch,parseDataDragonVersions,youtubeSearchUrl} from './resources'
import VideoResources from './VideoResources'
import {useI18n} from './i18n'
import {dataDragonVersions} from './dataDragon'

async function latestVersion(){return parseDataDragonVersions(await dataDragonVersions())}

export default function LearningResources({match,roleLabel}:{match:Match;roleLabel:string}){
 const {t}=useI18n()
 const matchPatch=normalizePatch(match.patch)
 const [current,setCurrent]=useState<ReturnType<typeof parseDataDragonVersions>|undefined>(),[searchPatch,setSearchPatch]=useState(matchPatch??'')
 useEffect(()=>{let active=true;void latestVersion().then(version=>{if(active)setCurrent(version)});return()=>{active=false}},[])
 useEffect(()=>{setSearchPatch(normalizePatch(match.patch)??'')},[match.id,match.patch])
 const searchRole=({TOP:'Top',JUNGLE:'Jungle',MIDDLE:'Mid',MID:'Mid',BOTTOM:'Bot',UTILITY:'Support',SUPPORT:'Support'}[match.role]??'Unknown role')
 const guide=youtubeSearchUrl(match.champion,searchRole,searchPatch,'guide'),otp=youtubeSearchUrl(match.champion,searchRole,searchPatch,'otp')
 const providers=[['OP.GG champion directory','https://op.gg/lol/champions'],['FOW','https://fow.lol/'],['GGQ','https://ggq.gg/'],['DEEPLOL','https://www.deeplol.gg/'],['YOUR.GG','https://your.gg/']]
 return <section className="panel learning-resources" aria-labelledby="learning-resources-title">
  <div className="panel-header"><div><h3 id="learning-resources-title"><BookOpen size={17}/>{t('Learning resources')}</h3><p>{match.champion} · {roleLabel} · {t('Resources for the selected match')}</p></div><span className="badge neutral">{t('External links')}</span></div>
  <div className="resources-body">
   <div className="resources-versions"><p>{t('Selected match patch:')} <strong>{matchPatch??t('Not available')}</strong>{match.patch&&matchPatch&&<span className="muted"> · {t('match version {version}',{version:match.patch})}</span>}</p><p aria-live="polite">{t('Data Dragon version:')} <strong>{current===undefined?t('Loading…'):current?.version??t('Unavailable')}</strong> <span className="muted">{t('(regional rollout may differ)')}</span></p></div>
   <p className="muted">{t('External sites, search on site for {champion} / {role}. These links open separate services; no player ID is sent.',{champion:match.champion,role:roleLabel})}</p>
   <div className="resource-links">{providers.map(([label,url])=><a className="secondary-button" href={url} target="_blank" rel="noopener noreferrer" key={url}>{t(label)}<ArrowUpRight size={14}/></a>)}</div>
   <div className="resource-search"><label htmlFor="resource-patch">{t('Patch for YouTube searches')}<input id="resource-patch" value={searchPatch} onChange={event=>setSearchPatch(event.target.value)} maxLength={40} placeholder={t('e.g. 16.21')} aria-invalid={!guide} aria-describedby="resource-search-note"/></label><button type="button" className="secondary-button" disabled={!matchPatch} onClick={()=>setSearchPatch(matchPatch??'')}>{t('Use match patch')}</button><button type="button" className="secondary-button" disabled={!current} onClick={()=>{if(current)setSearchPatch(current.patch)}}>{t('Use Data Dragon patch')}</button></div>
   {!guide&&<p className="resource-error" role="alert">{t('Enter a patch such as 16.21, or leave it empty to search without a patch.')}</p>}
   <div className="resource-links">{guide&&<a className="secondary-button" href={guide} target="_blank" rel="noopener noreferrer">{t('YouTube guide search')}<ArrowUpRight size={14}/></a>}{otp&&<a className="secondary-button" href={otp} target="_blank" rel="noopener noreferrer">{t('YouTube challenger / one-trick search')}<ArrowUpRight size={14}/></a>}</div>
   <p className="muted" id="resource-search-note">{t('Searches use the champion, role and entered patch. Results are not verified recommendations: video quality, view counts and patch coverage have not been checked.')}{!searchPatch.trim()?` ${t('No patch is included in the search.')}`:''}</p>
   <VideoResources champion={match.champion} role={searchRole} patch={normalizePatch(searchPatch)??''} valid={Boolean(guide)}/>
  </div>
 </section>
}
