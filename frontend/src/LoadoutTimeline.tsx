import type {LoadoutHistory} from './types'
import {useI18n} from './i18n'
import {elapsed} from './native'

const ACTIONS:Record<string,string>={ITEM_PURCHASED:'Purchased',ITEM_SOLD:'Sold',ITEM_DESTROYED:'Consumed or combined',ITEM_UNDO:'Undo'}
export default function LoadoutTimeline({history,names={}}:{history?:LoadoutHistory;names?:Record<string,string>}){
 const {t}=useI18n()
 if(!history||history.status==='unavailable')return <p>{t('Purchase and skill timing is unavailable without a matching timeline.')}</p>
 const itemName=(id?:number|null)=>id?names[String(id)]??`${t('Item IDs')}: ${id}`:'—'
 return <details><summary>{t('Purchase sequence and skill order')}</summary>
 <p className="muted">{t('Observed choices only. Components and consumables are included; sold items stay in the purchase history. This is not an optimal-build recommendation.')}</p>
 {history.status==='partial'&&<p role="status">{t('Some events are incomplete or an undo could not be resolved. This purchase sequence is excluded from trusted build aggregates.')}</p>}
 <h4>{t('Recorded skill levels')}</h4>{history.skill_order.length?<p>{history.skill_order.map((row,index)=><span key={index}>{index?' → ':''}{row.ability} <small>({elapsed(row.timestamp_ms)})</small></span>)}</p>:<p>{t('No normal skill-level events were recorded.')}</p>}
 <h4>{t('Purchase and undo log')}</h4>{history.item_events.length?<ol>{history.item_events.map((row,index)=><li key={index}>{elapsed(row.timestamp_ms)} · {t(ACTIONS[row.kind]??row.kind)} · {row.kind==='ITEM_UNDO'?`${itemName(row.before_id)} → ${itemName(row.after_id)}`:itemName(row.item_id)}{row.undone?` · ${t('Reversed by undo')}`:''}</li>)}</ol>:<p>{t('No item events were recorded.')}</p>}
 </details>
}
